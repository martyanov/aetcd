import asyncio
import uuid

from . import exceptions
from . import rtypes


class Lock:
    """A distributed lock.

    This can be used as a context manager, with the lock being acquired and
    released as you would expect:

    .. code-block:: python

        client = aetcd.Client()

        # Create a lock that expires after 20 seconds
        with client.lock(b'key', ttl=20) as lock:
            # do something that requires the lock
            print(lock.is_acquired())

            # refresh the timeout on the lease
            lock.refresh()

    :param aetcd.client.Client client:
        An instance of :class:`~aetcd.client.Client`

    :param bytes key:
        The key under which the lock will be stored.

    :param int ttl:
        Length of time for the lock to live for in seconds. The lock
        will be released after this time elapses, unless refreshed.
    """

    def __init__(self, client, key: bytes, ttl: int):
        self._client = client
        self.key = key
        self.ttl = ttl
        self.lease = None
        # Store uuid as bytes, since it avoids having to decode each time we
        # need to compare
        self.uuid = uuid.uuid1().bytes

    async def _try_acquire(self):
        self.lease = await self._client.lease(self.ttl)

        success, metadata = await self._client.transaction(
            compare=[
                self._client.transactions.create(self.key) == 0,
            ],
            success=[
                self._client.transactions.put(
                    self.key,
                    self.uuid,
                    lease=self.lease,
                ),
            ],
            failure=[
                self._client.transactions.get(self.key),
            ],
        )

        if success is True:
            self.revision = metadata[0].response_put.header.revision
            return True

        self.revision = metadata[0][0][1].mod_revision
        self.lease = None

        return False

    async def _wait_for_delete_event(self, timeout: int):
        try:
            await self._client.watch_once(
                self.key,
                timeout=timeout,
                start_revision=self.revision + 1,
                kind=rtypes.EventKind.DELETE,
            )
        except exceptions.WatchTimeoutError:
            return

    async def acquire(self, timeout: int = 10):
        """Acquire the lock.

        :param int timeout:
            Maximum time to wait before returning. ``None`` means
            forever, any other value equal or greater than 0 is
            the number of seconds.

        :return:
            ``True`` if the lock has been acquired, ``False`` otherwise.
        """
        loop = asyncio.get_running_loop()
        deadline = None
        if timeout is not None:
            deadline = loop.time() + timeout

        while True:
            if await self._try_acquire():
                return True

            if deadline is not None:
                remaining_timeout = max(deadline - loop.time(), 0)
                if remaining_timeout == 0:
                    return False
            else:
                remaining_timeout = None

            await self._wait_for_delete_event(remaining_timeout)

    async def release(self):
        """Release the lock."""
        success, _ = await self._client.transaction(
            compare=[
                self._client.transactions.value(self.key) == self.uuid,
            ],
            success=[self._client.transactions.delete(self.key)],
            failure=[],
        )

        return success

    async def refresh(self):
        """Refresh the time to live on this lock."""
        if self.lease is not None:
            return await self.lease.refresh()

        raise ValueError(f'no lease associated with this lock: {self.key!r}')

    async def is_acquired(self):
        """Check if this lock is currently acquired."""
        result = await self._client.get(self.key)

        if result is None:
            return False

        return result.value == self.uuid

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.release()
