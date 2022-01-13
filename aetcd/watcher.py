import asyncio
import logging
import typing

from . import exceptions
from . import rpc
from . import rtypes


log = logging.getLogger(__name__)


class WatcherCallback:
    """Represents the result of a callback watch operation."""

    def __init__(self, callback: typing.Callable):
        #: A callback function that will be called when new events are emitted.
        self.callback: typing.Callable = callback

        #: ID of the watcher.
        self.watch_id: typing.Optional[int] = None

        #: Get the previous key-value before the event happend.
        self.prev_kv: bool = False

        #: Error that was raised by the underlying machinery, if any.
        self.error: typing.Optional[Exception] = None


class Watcher:
    """Watch for events happening or that have happened.

    One watcher can watch on multiple key ranges, streaming events for several
    watches at once. The entire event history can be watched starting from the
    last compaction revision.

    .. note::
        The implementation is mostly for internal use, it is advised to use
        appropriate client watch methods.
    """

    def __init__(self, watchstub, timeout=None, metadata=None):
        self._timeout = timeout
        self._watchstub = watchstub
        self._metadata = metadata

        self._lock = asyncio.Lock()
        self._request_queue = asyncio.Queue(maxsize=10)
        self._request_handler = None
        self._request_handler_lock = asyncio.Lock()
        self._callbacks = {}
        self._new_callback = None
        self._new_callback_ready = asyncio.Condition(lock=self._lock)

    def _build_watch_create_request(
        self,
        key: bytes,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        kind: typing.Optional[rtypes.EventKind] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ):
        watch_create_request = rpc.WatchCreateRequest()

        watch_create_request.key = key

        if range_end is not None:
            watch_create_request.range_end = range_end

        if start_revision is not None:
            watch_create_request.start_revision = start_revision

        watch_create_request.progress_notify = progress_notify

        # We alter the behavior of watch filters to make its API a bit more
        # user-friendly, as there are only two type of events, put and
        # delete, we have three variants: all events, put-only events and
        # delete-only events.
        if kind is not None:
            if not isinstance(kind, rtypes.EventKind):
                raise TypeError(
                    f'an instance of EventKind should be provided, not {type(kind)}')

            if kind == rtypes.EventKind.PUT:
                watch_create_request.filters.append(rpc.WatchCreateRequest.FilterType.NODELETE)

            if kind == rtypes.EventKind.DELETE:
                watch_create_request.filters.append(rpc.WatchCreateRequest.FilterType.NOPUT)

        watch_create_request.prev_kv = prev_kv

        return rpc.WatchRequest(create_request=watch_create_request)

    def _build_watch_cancel_request(self, watch_id: int):
        watch_cancel_request = rpc.WatchCancelRequest()
        watch_cancel_request.watch_id = watch_id
        return rpc.WatchRequest(cancel_request=watch_cancel_request)

    async def _enqueue_watch_create(self, *args, **kwargs):
        watch_create_request = self._build_watch_create_request(*args, **kwargs)
        await self._request_queue.put(watch_create_request)

    async def _enqueue_watch_cancel(self, *args, **kwargs):
        watch_cancel_request = self._build_watch_cancel_request(*args, **kwargs)
        await self._request_queue.put(watch_cancel_request)

    async def _process_callback(self, callback, event_or_error):
        try:
            await callback.callback(event_or_error)
        except Exception as e:
            log.exception(f'watch callback failed with {e!r}')

    async def _handle_response(self, response):
        async with self._lock:
            if response.created:
                # If the new watch request has already expired then cancel the
                # created watch right away.
                if not self._new_callback:
                    await self._enqueue_watch_cancel(watch_id=response.watch_id)
                    return

                if response.compact_revision != 0:
                    self._new_callback.error = exceptions.RevisionCompactedError(
                        response.compact_revision)
                    return

                self._callbacks[response.watch_id] = self._new_callback
                self._new_callback.watch_id = response.watch_id
                self._new_callback_ready.notify_all()

            watcher_callback = self._callbacks.get(response.watch_id)

        # Ignore leftovers from canceled watches.
        if watcher_callback is None:
            return

        # The watcher can be safely reused, but adding a new event
        # to indicate that the revision is already compacted
        # requires api change which would break all users of this
        # module. So, raising an exception if a watcher is still
        # alive.
        if response.compact_revision != 0:
            error = exceptions.RevisionCompactedError(response.compact_revision)
            await self._process_callback(watcher_callback, error)
            await self.cancel(response.watch_id)
            return

        for event in response.events:
            await self._process_callback(
                watcher_callback,
                rtypes.Event(
                    event.type,
                    event.kv,
                    event.prev_kv if watcher_callback.prev_kv else None,
                ),
            )

    async def _terminate_stream(self, error):
        # TODO: Refactor this machinery to handle each case separately,
        #       instead of one-for-all cases solution
        async with self._lock:
            if self._new_callback is not None:
                self._new_callback.error = error
                self._new_callback_ready.notify_all()

            callbacks = self._callbacks
            self._callbacks = {}

            # Rotate request queue. This way we can terminate one RPC
            # stream and initiate another one whilst avoiding a race
            # between them over requests in the queue
            await self._request_queue.put(None)
            self._request_queue = asyncio.Queue(maxsize=10)

        # Deliver error to all subscribers
        for callback in callbacks.values():
            await self._process_callback(callback, error)

        # Shutdown the watcher request handler
        async with self._request_handler_lock:
            if self._request_handler is not None:
                self._request_handler.cancel()
                try:
                    await self._request_handler
                except asyncio.CancelledError:
                    pass

                self._request_handler = None

    async def _iter_request(self):
        while True:
            request = await self._request_queue.get()

            if request is None:
                break

            yield request

    async def _handle_request(self, metadata):
        try:
            async for response in self._watchstub.Watch(
                self._iter_request(),
                metadata=metadata,
            ):
                if response is None:
                    break

                await self._handle_response(response)
        except Exception as e:
            await self._terminate_stream(e)

    async def setup(self):
        """Set up the watcher."""
        async with self._request_handler_lock:
            if self._request_handler is not None:
                return

            self._request_handler = asyncio.get_running_loop().create_task(
                self._handle_request(self._metadata),
            )

    async def shutdown(self):
        """Shutdown the watcher."""
        await self._terminate_stream(None)

    async def add_callback(
        self,
        key: bytes,
        callback: typing.Callable,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        kind: typing.Optional[rtypes.EventKind] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ) -> WatcherCallback:
        """Add a callback that will be called when new events are emitted.

        :param bytes key:
            Key to watch.

        :param callable callback:
            Callback function.

        :param bytes range_end:
            End of the range ``[key, range_end)`` to watch.
            If ``range_end`` is not given, only the ``key`` argument is watched.
            If ``range_end`` is equal to ``x00``, all keys greater than or equal
            to the ``key`` argument are watched.
            If the ``range_end`` is one bit larger than the given ``key``,
            then all keys with the prefix (the given ``key``) will be watched.

        :param int start_revision:
            Revision to watch from (inclusive).

        :param bool progress_notify:
            If set, the server will periodically send a response with
            no events to the new watcher if there are no recent events. It is
            useful when clients wish to recover a disconnected watcher starting
            from a recent known revision. The server may decide how often it will
            send notifications based on the current load.

        :param aetcd.rtypes.EventKind kind:
            Filter the events by :class:`~aetcd.rtypes.EventKind`,
            at server side before it sends back to the watcher.

        :param bool prev_kv:
            If set, created watcher gets the previous key-value before the event happend.
            If the previous key-value is already compacted, nothing will be returned.

        :param int watch_id:
            If provided and non-zero, it will be assigned as ID to this watcher.
            Since creating a watcher in ``etcd`` is not a synchronous operation,
            this can be used ensure that ordering is correct when creating multiple
            watchers on the same stream. Creating a watcher with an ID already in
            use on the stream will cause an error to be returned.

        :param bool fragment:
            Enable splitting large revisions into multiple watch responses.

        :return:
            A instance of :class:`~aetcd.watch.WatcherCallback`.
        """
        async with self._lock:
            await self.setup()

            # Only one callback create request can be pending at a time, so if
            # there one already, then wait for it to complete first
            while self._new_callback:
                await self._new_callback_ready.wait()

            # Create callback and submit a create watch request
            # TODO: Extend with additional watch related fields
            watcher_callback = WatcherCallback(callback)
            watcher_callback.prev_kv = prev_kv
            self._new_callback = watcher_callback
            await self._enqueue_watch_create(
                key,
                range_end=range_end,
                start_revision=start_revision,
                progress_notify=progress_notify,
                kind=kind,
                prev_kv=prev_kv,
                watch_id=watch_id,
                fragment=fragment,
            )

            try:
                # Wait for the request to be completed or timeout
                try:
                    await asyncio.wait_for(self._new_callback_ready.wait(), self._timeout)
                except asyncio.TimeoutError:
                    raise exceptions.WatchTimeoutError

                # If the request not completed yet, then raise a timeout
                # exception
                if self._new_callback.watch_id is None and self._new_callback.error is None:
                    raise exceptions.WatchTimeoutError

                # Raise an exception if the watch request failed
                if self._new_callback.error is not None:
                    raise self._new_callback.error
            finally:
                # Wake up all coroutines waiting on add_callback call, if any
                self._new_callback = None
                self._new_callback_ready.notify_all()

            return watcher_callback

    async def cancel(self, watch_id: int) -> None:
        """Cancel the watcher so that no more events are emitted.

        :param int watch_id:
            The ID of the watcher to cancel.
        """
        async with self._lock:
            callback = self._callbacks.pop(watch_id, None)
            if callback is None:
                return

            await self._enqueue_watch_cancel(watch_id=watch_id)
