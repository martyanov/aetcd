import asyncio
import logging
import typing

from . import events
from . import exceptions
from . import rpc
from . import utils


log = logging.getLogger(__name__)


async def _process_callback(callback, event_or_err):
    try:
        await callback(event_or_err)
    except Exception as e:
        log.exception(f'watch callback failed with {e!r}')


class _WatchCallback:
    def __init__(self, callback):
        self.callback = callback
        self.id = None
        self.err = None


class Watcher(object):

    def __init__(self, watchstub, timeout=None, metadata=None):
        self.timeout = timeout
        self._watchstub = watchstub
        self._metadata = metadata

        self._lock = asyncio.Lock()
        self._request_queue = asyncio.Queue(maxsize=10)
        self._callbacks = {}
        self._request_handler = None
        self._new_watch_cond = asyncio.Condition(lock=self._lock)
        self._new_watch = None

    def _build_watch_create_request(
        self,
        key: bytes,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        filters: typing.Optional[typing.List] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ):
        watch_create_request = rpc.WatchCreateRequest()

        watch_create_request.key = utils.to_bytes(key)

        if range_end is not None:
            watch_create_request.range_end = range_end

        if start_revision is not None:
            watch_create_request.start_revision = start_revision

        watch_create_request.progress_notify = progress_notify

        if filters is not None:
            watch_create_request.filters.extend(filters)

        watch_create_request.prev_kv = prev_kv

        return rpc.WatchRequest(create_request=watch_create_request)

    def _build_watch_cancel_request(self, watch_id: int):
        watch_cancel_request = rpc.WatchCancelRequest()
        watch_cancel_request.watch_id = watch_id
        return rpc.WatchRequest(cancel_request=watch_cancel_request)

    async def _enqueue_watch_create(self, *args, **kwargs):
        watch_create_request = self._build_watch_create_request(*args, **kwargs)
        await self._request_queue.put(watch_create_request)

    async def _enqueue_watch_cancel(self, **kwargs):
        watch_cancel_request = self._build_watch_cancel_request(**kwargs)
        await self._request_queue.put(watch_cancel_request)

    async def _handle_response(self, rs):
        async with self._lock:
            if rs.created:
                # If the new watch request has already expired then cancel the
                # created watch right away.
                if not self._new_watch:
                    await self._enqueue_watch_cancel(watch_id=rs.watch_id)
                    return

                if rs.compact_revision != 0:
                    self._new_watch.err = exceptions.RevisionCompactedError(
                        rs.compact_revision)
                    return

                self._callbacks[rs.watch_id] = self._new_watch.callback
                self._new_watch.id = rs.watch_id
                self._new_watch_cond.notify_all()

            callback = self._callbacks.get(rs.watch_id)

        # Ignore leftovers from canceled watches.
        if not callback:
            return

        # The watcher can be safely reused, but adding a new event
        # to indicate that the revision is already compacted
        # requires api change which would break all users of this
        # module. So, raising an exception if a watcher is still
        # alive.
        if rs.compact_revision != 0:
            err = exceptions.RevisionCompactedError(rs.compact_revision)
            await _process_callback(callback, err)
            await self.cancel(rs.watch_id)
            return

        for event in rs.events:
            await _process_callback(callback, events.new_event(event))

    async def _handle_stream_termination(self, err):
        async with self._lock:
            if self._new_watch:
                self._new_watch.err = err
                self._new_watch_cond.notify_all()

            callbacks = self._callbacks
            self._callbacks = {}

            # Rotate request queue. This way we can terminate one gRPC
            # stream and initiate another one whilst avoiding a race
            # between them over requests in the queue
            await self._request_queue.put(None)
            self._request_queue = asyncio.Queue(maxsize=10)
        for callback in callbacks.values():
            await _process_callback(callback, err)

    async def _iter_request(self):
        while True:
            request = await self._request_queue.get()

            if request is None:
                break

            yield request

    async def _handle_request(self, timeout, metadata):
        try:
            async for response in self._watchstub.Watch(
                self._iter_request(),
                timeout=timeout,
                metadata=metadata,
            ):
                if response is None:
                    break

                await self._handle_response(response)
        except Exception as e:
            await self._handle_stream_termination(e)

    async def setup(self):
        """Set up the watcher."""
        if self._request_handler is not None:
            return

        self._request_handler = asyncio.get_running_loop().create_task(
            self._handle_request(self.timeout, self._metadata),
        )

    async def shutdown(self):
        """Shutdown the watcher."""
        if self._request_handler:
            self._request_handler.cancel()
            try:
                await self._request_handler
            except asyncio.CancelledError:
                pass

        self._request_handler = None

    async def add_callback(
        self,
        key,
        callback,
        range_end=None,
        start_revision=None,
        progress_notify=False,
        filters=None,
        prev_kv=False,
    ):
        async with self._lock:
            await self.setup()

            # Only one create watch request can be pending at a time, so if
            # there one already, then wait for it to complete first
            while self._new_watch:
                await self._new_watch_cond.wait()

            # Submit a create watch request
            new_watch = _WatchCallback(callback)
            self._new_watch = new_watch
            await self._enqueue_watch_create(
                key,
                range_end=range_end,
                start_revision=start_revision,
                progress_notify=progress_notify,
                filters=filters,
                prev_kv=prev_kv,
            )

            try:
                # Wait for the request to be completed or timeout
                try:
                    await asyncio.wait_for(self._new_watch_cond.wait(), self.timeout)
                except asyncio.TimeoutError:
                    raise exceptions.WatchTimeoutError

                # If the request not completed yet, then raise a timeout
                # exception
                if new_watch.id is None and new_watch.err is None:
                    raise exceptions.WatchTimeoutError

                # Raise an exception if the watch request failed
                if new_watch.err:
                    raise new_watch.err
            finally:
                # Wake up all coroutines waiting on add_callback call, if any
                self._new_watch = None
                self._new_watch_cond.notify_all()

            return new_watch.id

    async def cancel(self, watch_id: int) -> None:
        async with self._lock:
            callback = self._callbacks.pop(watch_id, None)
            if callback is None:
                return

            await self._enqueue_watch_cancel(watch_id=watch_id)
