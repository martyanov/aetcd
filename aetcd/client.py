import asyncio
import functools
import inspect
import typing

from . import exceptions
from . import leases
from . import locks
from . import members
from . import rpc
from . import rtypes
from . import transactions
from . import utils
from . import watcher


def _handle_errors(f):
    if inspect.iscoroutinefunction(f):
        async def handler(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except rpc.AioRpcError as e:
                exceptions._handle_exception(e)
    elif inspect.isasyncgenfunction(f):
        async def handler(*args, **kwargs):
            try:
                async for data in f(*args, **kwargs):
                    yield data
            except rpc.AioRpcError as e:
                exceptions._handle_exception(e)
    else:
        raise RuntimeError(
            f'provided function {f.__name__!r} is neither a coroutine nor an async generator')

    return functools.wraps(f)(handler)


def _ensure_connected(f):
    if inspect.iscoroutinefunction(f):
        async def handler(self, *args, **kwargs):
            await self.connect()
            return await f(self, *args, **kwargs)
    elif inspect.isasyncgenfunction(f):
        async def handler(self, *args, **kwargs):
            await self.connect()
            async for data in f(self, *args, **kwargs):
                yield data
    else:
        raise RuntimeError(
            f'provided function {f.__name__!r} is neither a coroutine nor an async generator')

    return functools.wraps(f)(handler)


class Transactions:
    def __init__(self):
        self.value = transactions.Value
        self.version = transactions.Version
        self.create = transactions.Create
        self.mod = transactions.Mod

        self.put = transactions.Put
        self.get = transactions.Get
        self.delete = transactions.Delete
        self.txn = transactions.Txn


class Status:
    def __init__(self, version, db_size, leader, raft_index, raft_term):
        self.version = version
        self.db_size = db_size
        self.leader = leader
        self.raft_index = raft_index
        self.raft_term = raft_term


class Alarm:
    """A cluster member alarm.

    :param alarm_type:
        Type of the alarm.

    :param member_id:
        Cluster member ID.
    """

    def __init__(self, alarm_type, member_id):
        self.alarm_type = alarm_type
        self.member_id = member_id


class Client:
    """Client provides and manages a client session.

    The client can be used as an async context manager.

    :param str host:
        etcd host address, as IP address or a domain name.

    :param int port:
        etcd port number to connect to.

    :param str username:
        The name of the  user used for authentication.

    :param str password:
        Password to be used for authentication.

    :param int timeout:
        Connection timeout in seconds.

    :param dict options:
        Options provided to the underlying gRPC channel.

    :param int connect_wait_timeout:
        Connecting wait timeout, since connection could be initiated
        from multiple coroutines.

    :return:
        A :class:`~aetcd.client.Client` instance.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 2379,
        username: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        timeout: typing.Optional[int] = None,
        options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        connect_wait_timeout: int = 3,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self._options = options or {}
        self._connect_wait_timeout = connect_wait_timeout
        self._connected = asyncio.Event()
        self._is_connecting = False

        cred_params = (self._username, self._password)
        if any(cred_params) and None in cred_params:
            raise Exception(
                'if using authentication credentials both username and password '
                'must be provided')

        self._init_channel_attrs()

        self.transactions = Transactions()

    def _init_channel_attrs(self):
        # These attributes will be assigned during opening of GRPC channel
        self.channel = None
        self.metadata = None
        self.auth_stub = None
        self.kvstub = None
        self.clusterstub = None
        self.leasestub = None
        self.maintenancestub = None

        self._watcher = None

    @_handle_errors
    async def connect(self) -> None:
        """Establish a connection to an etcd."""
        if self._connected.is_set():
            return

        if self._is_connecting:
            # Another task is establishing a connection, just wait
            await asyncio.wait_for(
                self._connected.wait(),
                self._connect_wait_timeout,
            )
            return

        try:
            self._is_connecting = True
            target = f'{self._host}:{self._port}'
            self.channel = rpc.insecure_channel(target, options=self._options.items())

            cred_params = [c is not None for c in (self._username, self._password)]
            if all(cred_params):
                self.auth_stub = rpc.AuthStub(self.channel)
                auth_request = rpc.AuthenticateRequest(
                    name=self._username,
                    password=self._password,
                )

                resp = await self.auth_stub.Authenticate(auth_request, timeout=self._timeout)
                self.metadata = (('token', resp.token),)

            self.kvstub = rpc.KVStub(self.channel)
            self.clusterstub = rpc.ClusterStub(self.channel)
            self.leasestub = rpc.LeaseStub(self.channel)
            self.maintenancestub = rpc.MaintenanceStub(self.channel)

            # Initialize a watcher
            self._watcher = watcher.Watcher(
                rpc.WatchStub(self.channel),
                timeout=self._timeout,
                metadata=self.metadata,
            )

            self._connected.set()
        finally:
            self._is_connecting = False

    async def close(self) -> None:
        """Close established connection and frees allocated resources.

        It could be called while other operation is being executed.
        """
        if not self._connected.is_set() and self._is_connecting:
            # Wait for the previous request to complete
            await asyncio.wait_for(
                self._connected.wait(),
                self._connect_wait_timeout,
            )

        if self.channel:
            # Shutdown the watcher
            if self._watcher is not None:
                await self._watcher.shutdown()

            # Close the underlying RPC channel
            if self.channel:
                # Check it again since it could be modified by a concurrent task
                await self.channel.close()

            self._init_channel_attrs()

        self._connected.clear()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()

    @_handle_errors
    @_ensure_connected
    async def get(
        self,
        key: bytes,
        serializable: bool = False,
    ) -> typing.Optional[rtypes.Get]:
        """Get a single key from the key-value store.

        :param bytes key:
            Key in etcd to get.

        :param bool serializable:
            Whether to allow serializable reads. This can result in stale reads.

        :return:
            A instance of :class:`~aetcd.rtypes.Get` or ``None``, if the
            the key was not found.

        Usage example:

        .. code-block:: python

            import aetcd
            client = aetcd.Client()
            await client.get(b'key')
        """
        range_request = self._build_get_range_request(
            key,
            serializable=serializable,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        if range_response.count < 1:
            return None

        return rtypes.Get(range_response.header, range_response.kvs.pop())

    @_handle_errors
    @_ensure_connected
    async def get_prefix(
        self,
        key_prefix: bytes,
        sort_order: typing.Optional[str] = None,
        sort_target: str = 'key',
        keys_only: bool = False,
    ) -> rtypes.GetRange:
        """Get a range of keys with a prefix from the key-value store.

        :param bytes key_prefix:
            Key prefix to get.

        :return:
            An instance of :class:`~aetcd.rtypes.GetRange`.
        """
        range_request = self._build_get_range_request(
            key=key_prefix,
            range_end=utils.prefix_range_end(key_prefix),
            sort_order=sort_order,
            sort_target=sort_target,
            keys_only=keys_only,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.GetRange(
            range_response.header,
            range_response.kvs,
            range_response.more,
            range_response.count,
        )

    @_handle_errors
    @_ensure_connected
    async def get_range(
        self,
        range_start: bytes,
        range_end: bytes,
        sort_order: typing.Optional[str] = None,
        sort_target: str = 'key',
    ) -> rtypes.GetRange:
        """Get a range of keys from the key-value store.

        :param bytes range_start:
            First key in range.

        :param bytes range_end:
            Last key in range.

        :return:
            An instance of :class:`~aetcd.rtypes.GetRange`.
        """
        range_request = self._build_get_range_request(
            key=range_start,
            range_end=range_end,
            sort_order=sort_order,
            sort_target=sort_target,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.GetRange(
            range_response.header,
            range_response.kvs,
            range_response.more,
            range_response.count,
        )

    @_handle_errors
    @_ensure_connected
    async def get_all(
        self,
        sort_order=None,
        sort_target='key',
        keys_only=False,
    ) -> rtypes.GetRange:
        """Get all keys from the key-value store.

        :return:
            An instance of :class:`~aetcd.rtypes.GetRange`.
        """
        range_request = self._build_get_range_request(
            key=b'\0',
            range_end=b'\0',
            sort_order=sort_order,
            sort_target=sort_target,
            keys_only=keys_only,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.GetRange(
            range_response.header,
            range_response.kvs,
            range_response.more,
            range_response.count,
        )

    @_handle_errors
    @_ensure_connected
    async def put(
        self,
        key: bytes,
        value: bytes,
        lease: typing.Optional[typing.Union[int, leases.Lease]] = None,
        prev_kv: bool = False,
    ) -> rtypes.Put:
        """Put the given key into the key-value store.

        :param bytes key:
            Key in etcd to set.

        :param bytes value:
            Value to set key to.

        :param lease:
            Lease to associate with this key.
        :type lease:
            either :class:`~aetcd.leases.Lease`, or ``int`` (ID of a lease), or ``None``

        :param bool prev_kv:
            Whether to return the previous key-value pair.

        :return:
            A instance of :class:`~aetcd.rtypes.Put`.

        Usage example:

        .. code-block:: python

            import aetcd
            client = aetcd.Client()
            await client.put(b'key', b'value')
        """
        put_request = self._build_put_request(
            key,
            value,
            lease=lease,
            prev_kv=prev_kv,
        )

        put_response = await self.kvstub.Put(
            put_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.Put(
            put_response.header,
            put_response.prev_kv if prev_kv else None,
        )

    @_handle_errors
    @_ensure_connected
    async def delete(
        self,
        key: bytes,
        prev_kv: bool = False,
    ) -> typing.Optional[rtypes.Delete]:
        """Delete a single key from the key-value store.

        :param bytes key:
            Key in etcd to delete.

        :param bool prev_kv:
            Whether to return the deleted key-value pair.

        :return:
            A instance of :class:`~aetcd.rtypes.Delete` or ``None``, if the
            the key was not found.

        Usage example:

        .. code-block:: python

            import aetcd
            client = aetcd.Client()
            await client.put(b'key', b'value')
            await client.delete(b'key')
        """
        delete_request = self._build_delete_request(key, prev_kv=prev_kv)

        delete_response = await self.kvstub.DeleteRange(
            delete_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        if delete_response.deleted < 1:
            return None

        return rtypes.Delete(
            delete_response.header,
            delete_response.deleted,
            delete_response.prev_kvs.pop() if prev_kv else None,
        )

    @_handle_errors
    @_ensure_connected
    async def delete_prefix(
        self,
        key_prefix: bytes,
        prev_kv: bool = False,
    ) -> rtypes.DeleteRange:
        """Delete a range of keys with a prefix from the key-value store.

        :param bytes key_prefix:
            Key prefix to delete.

        :param bool prev_kv:
            Whether to return deleted key-value pairs.

        :return:
            An instance of :class:`~aetcd.rtypes.DeleteRange`.
        """
        delete_request = self._build_delete_request(
            key_prefix,
            range_end=utils.prefix_range_end(key_prefix),
            prev_kv=prev_kv,
        )

        delete_response = await self.kvstub.DeleteRange(
            delete_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.DeleteRange(
            delete_response.header,
            delete_response.deleted,
            delete_response.prev_kvs,
        )

    @_handle_errors
    @_ensure_connected
    async def delete_range(
        self,
        range_start: bytes,
        range_end: bytes,
        prev_kv: bool = False,
    ) -> rtypes.DeleteRange:
        """Delete a range of keys from the key-value store.

        :param bytes range_start:
            First key in range.

        :param bytes range_end:
            Last key in range.

        :param bool prev_kv:
            Whether to return deleted key-value pairs.

        :return:
            An instance of :class:`~aetcd.rtypes.DeleteRange`.
        """
        delete_request = self._build_delete_request(
            range_start,
            range_end=range_end,
            prev_kv=prev_kv,
        )

        delete_response = await self.kvstub.DeleteRange(
            delete_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return rtypes.DeleteRange(
            delete_response.header,
            delete_response.deleted,
            delete_response.prev_kvs,
        )

    async def replace(
        self,
        key: bytes,
        initial_value: bytes,
        new_value: bytes,
        lease: typing.Optional[typing.Union[int, leases.Lease]] = None,
    ):
        """Atomically replace the value of a key with a new value.

        This compares the current value of a key, then replaces it with a new
        value if it is equal to a specified value. This operation takes place
        in a transaction.

        :param key:
            Key in etcd to replace.

        :param bytes initial_value:
            Old value to replace.

        :param bytes new_value:
            New value of the key

        :param lease:
            Lease to associate with this key.
        :type lease:
            either :class:`~aetcd.leases.Lease`, or ``int`` (ID of a lease), or ``None``

        :return:
            A status of transaction, ``True`` if the replace was successful,
            ``False`` otherwise.
        """
        status, _ = await self.transaction(
            compare=[
                self.transactions.value(key) == initial_value,
            ],
            success=[
                self.transactions.put(key, new_value, lease=lease),
            ],
            failure=[],
        )

        return status

    @_handle_errors
    @_ensure_connected
    async def watch(
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
        """Watch a key.

        :param bytes key:
            Key to watch.

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
            no events to the new watcher if there are no recent events.

        :param aetcd.rtypes.EventKind kind:
            Filter the events by :class:`~aetcd.rtypes.EventKind`,
            at server side before it sends back to the watcher.

        :param bool prev_kv:
            If set, created watcher gets the previous key-value before the event happend.
            If the previous key-value is already compacted, nothing will be returned.

        :param int watch_id:
            If provided and non-zero, it will be assigned as ID to this watcher.

        :param bool fragment:
            Enable splitting large revisions into multiple watch responses.

        :return:
            A instance of :class:`~aetcd.rtypes.Watch`.

        Usage example:

        .. code-block:: python

            async for event in await client.watch(b'key'):
                print(event)
        """
        events = asyncio.Queue()

        async def response_callback(response):
            await events.put(response)

        watcher_callback = await self._watcher.add_callback(
            key,
            response_callback,
            range_end=range_end,
            start_revision=start_revision,
            progress_notify=progress_notify,
            kind=kind,
            prev_kv=prev_kv,
            watch_id=watch_id,
            fragment=fragment,
        )
        canceled = asyncio.Event()

        async def cancel():
            canceled.set()
            await events.put(None)
            await self._watcher.cancel(watcher_callback.watch_id)

        @_handle_errors
        async def iterator():
            while not canceled.is_set():
                event = await events.get()
                if event is None:
                    canceled.set()
                if isinstance(event, Exception):
                    canceled.set()
                    raise event
                if not canceled.is_set():
                    yield event

        return rtypes.Watch(
            iterator,
            cancel,
            watcher_callback.watch_id,
        )

    async def watch_prefix(
        self,
        key_prefix: bytes,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        kind: typing.Optional[rtypes.EventKind] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ):
        """Watch a range of keys with a prefix.

        :param bytes key_prefix:
            Key prefix to watch.

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
            no events to the new watcher if there are no recent events.

        :param aetcd.rtypes.EventKind kind:
            Filter the events by :class:`~aetcd.rtypes.EventKind`,
            at server side before it sends back to the watcher.

        :param bool prev_kv:
            If set, created watcher gets the previous key-value before the event happend.
            If the previous key-value is already compacted, nothing will be returned.

        :param int watch_id:
            If provided and non-zero, it will be assigned as ID to this watcher.

        :param bool fragment:
            Enable splitting large revisions into multiple watch responses.

        :return:
            A instance of :class:`~aetcd.rtypes.Watch`.
        """
        return await self.watch(
            key_prefix,
            range_end=utils.prefix_range_end(key_prefix),
            start_revision=start_revision,
            progress_notify=progress_notify,
            kind=kind,
            prev_kv=prev_kv,
            watch_id=watch_id,
            fragment=fragment,
        )

    @_handle_errors
    @_ensure_connected
    async def watch_once(
        self,
        key: bytes,
        timeout: typing.Optional[int] = None,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        kind: typing.Optional[rtypes.EventKind] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ):
        """Watch a key and stops after the first event.

        If the timeout was specified and event didn't arrived method
        will raise ``WatchTimeoutError`` exception.

        :param bytes key:
            Key to watch.

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
            no events to the new watcher if there are no recent events.

        :param aetcd.rtypes.EventKind kind:
            Filter the events by :class:`~aetcd.rtypes.EventKind`,
            at server side before it sends back to the watcher.

        :param bool prev_kv:
            If set, created watcher gets the previous key-value before the event happend.
            If the previous key-value is already compacted, nothing will be returned.

        :param int watch_id:
            If provided and non-zero, it will be assigned as ID to this watcher.

        :param bool fragment:
            Enable splitting large revisions into multiple watch responses.

        :return:
            An instance of :class:`~aetcd.rtypes.Event`.
        """
        event_queue = asyncio.Queue()

        watcher_callback = await self._watcher.add_callback(
            key,
            event_queue.put,
            range_end=range_end,
            start_revision=start_revision,
            progress_notify=progress_notify,
            kind=kind,
            prev_kv=prev_kv,
            watch_id=watch_id,
            fragment=fragment,
        )

        try:
            return await asyncio.wait_for(event_queue.get(), timeout)
        except asyncio.TimeoutError:
            raise exceptions.WatchTimeoutError
        finally:
            await self._watcher.cancel(watcher_callback.watch_id)

    async def watch_prefix_once(
        self,
        key_prefix: bytes,
        timeout: typing.Optional[int] = None,
        range_end: typing.Optional[bytes] = None,
        start_revision: typing.Optional[int] = None,
        progress_notify: bool = False,
        kind: typing.Optional[rtypes.EventKind] = None,
        prev_kv: bool = False,
        watch_id: typing.Optional[int] = None,
        fragment: bool = False,
    ):
        """Watch a range of keys with a prefix and stops after the first event.

        If the timeout was specified and event didn't arrived method
        will raise ``WatchTimeoutError`` exception.

        :param bytes key_prefix:
            Key prefix to watch.

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
            no events to the new watcher if there are no recent events.

        :param aetcd.rtypes.EventKind kind:
            Filter the events by :class:`~aetcd.rtypes.EventKind`,
            at server side before it sends back to the watcher.

        :param bool prev_kv:
            If set, created watcher gets the previous key-value before the event happend.
            If the previous key-value is already compacted, nothing will be returned.

        :param int watch_id:
            If provided and non-zero, it will be assigned as ID to this watcher.

        :param bool fragment:
            Enable splitting large revisions into multiple watch responses.

        :return:
            An instance of :class:`~aetcd.rtypes.Event`.
        """
        return await self.watch_once(
            key_prefix,
            timeout=timeout,
            range_end=utils.prefix_range_end(key_prefix),
            start_revision=start_revision,
            progress_notify=progress_notify,
            kind=kind,
            prev_kv=prev_kv,
            watch_id=watch_id,
            fragment=fragment,
        )

    @_handle_errors
    @_ensure_connected
    async def transaction(self, compare, success=None, failure=None):
        """Perform a transaction.

        :param compare:
            A list of comparisons to make

        :param success:
            A list of operations to perform if all the comparisons
            are true.

        :param failure:
            A list of operations to perform if any of the
            comparisons are false.

        :return:
            A tuple of (operation status, responses).

        Usage example:

        .. code-block:: python

            await client.transaction(
                compare=[
                    client.transactions.value(b'key') == b'value',
                    client.transactions.version(b'key') > 0,
                ],
                success=[
                    client.transactions.put(b'key', b'success'),
                ],
                failure=[
                    client.transactions.put(b'key', b'failure'),
                ]
            )
        """
        compare = [c.build_message() for c in compare]

        success_ops = self._ops_to_requests(success)
        failure_ops = self._ops_to_requests(failure)

        transaction_request = rpc.TxnRequest(
            compare=compare,
            success=success_ops,
            failure=failure_ops,
        )
        txn_response = await self.kvstub.Txn(
            transaction_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        responses = []
        for response in txn_response.responses:
            response_type = response.WhichOneof('response')
            if response_type in ['response_put', 'response_delete_range', 'response_txn']:
                responses.append(response)

            elif response_type == 'response_range':
                range_kvs = []
                for kv in response.response_range.kvs:
                    range_kvs.append(
                        (
                            kv.value,
                            rtypes.Get(txn_response.header, kv),
                        ),
                    )

                responses.append(range_kvs)

        return txn_response.succeeded, responses

    @_handle_errors
    @_ensure_connected
    async def lease(self, ttl, lease_id=None):
        """Create a new lease.

        All keys attached to this lease will be expired and deleted if the
        lease expires. A lease can be sent keep alive messages to refresh the
        ttl.

        :param int ttl:
            Requested time to live.

        :param lease_id:
            Requested ID for the lease.

        :return:
            A new lease, an instance of :class:`~aetcd.leases.Lease`.
        """
        lease_grant_request = rpc.LeaseGrantRequest(TTL=ttl, ID=lease_id)
        lease_grant_response = await self.leasestub.LeaseGrant(
            lease_grant_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )
        return leases.Lease(
            lease_id=lease_grant_response.ID,
            ttl=lease_grant_response.TTL,
            etcd_client=self,
        )

    @_handle_errors
    @_ensure_connected
    async def revoke_lease(self, lease_id):
        """Revoke a lease.

        :param lease_id:
            ID of the lease to revoke.
        """
        lease_revoke_request = rpc.LeaseRevokeRequest(ID=lease_id)
        await self.leasestub.LeaseRevoke(
            lease_revoke_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_handle_errors
    @_ensure_connected
    async def refresh_lease(self, lease_id):
        async for reply in self.leasestub.LeaseKeepAlive(
            [rpc.LeaseKeepAliveRequest(ID=lease_id)],
            timeout=self._timeout,
            metadata=self.metadata,
        ):
            return reply

    @_handle_errors
    @_ensure_connected
    async def get_lease_info(self, lease_id, *, keys=True):
        ttl_request = rpc.LeaseTimeToLiveRequest(
            ID=lease_id,
            keys=keys,
        )
        return await self.leasestub.LeaseTimeToLive(
            ttl_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    def lock(self, key: bytes, ttl: int = 60):
        """Create a new lock.

        :param bytes key:
            The key under which the lock will be stored.

        :param int ttl:
            Length of time for the lock to live for in seconds. The
            lock will be released after this time elapses, unless refreshed.

        :return:
            A new lock, an instance of :class:`~aetcd.locks.Lock`.
        """
        return locks.Lock(self, key, ttl)

    @_handle_errors
    @_ensure_connected
    async def status(self):
        """Get the status of the responding member."""
        status_request = rpc.StatusRequest()
        status_response = await self.maintenancestub.Status(
            status_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        async for m in self.members():
            if m.id == status_response.leader:
                leader = m
                break
        else:
            # raise exception?
            leader = None

        return Status(
            status_response.version,
            status_response.dbSize,
            leader,
            status_response.raftIndex,
            status_response.raftTerm,
        )

    @_handle_errors
    @_ensure_connected
    async def add_member(self, urls):
        """Add a member into the cluster.

        :return:
            A new member, an instance of :class:`~aetcd.members.Member`.
        """
        member_add_request = rpc.MemberAddRequest(peerURLs=urls)

        member_add_response = await self.clusterstub.MemberAdd(
            member_add_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        member = member_add_response.member
        return members.Member(
            member.ID,
            member.name,
            member.peerURLs,
            member.clientURLs,
            etcd_client=self,
        )

    @_handle_errors
    @_ensure_connected
    async def remove_member(self, member_id):
        """Remove an existing member from the cluster.

        :param member_id:
            ID of the member to remove.
        """
        member_rm_request = rpc.MemberRemoveRequest(ID=member_id)
        await self.clusterstub.MemberRemove(
            member_rm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_handle_errors
    @_ensure_connected
    async def update_member(self, member_id, peer_urls):
        """Update the configuration of an existing member in the cluster.

        :param member_id:
            ID of the member to update.

        :param peer_urls:
            New list of peer URLs the member will use to
            communicate with the cluster.
        """
        member_update_request = rpc.MemberUpdateRequest(
            ID=member_id,
            peerURLs=peer_urls,
        )
        await self.clusterstub.MemberUpdate(
            member_update_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_ensure_connected
    async def members(self):
        """List of all members associated with the cluster.

        :return:
            A sequence of :class:`~aetcd.members.Member`.

        """
        member_list_request = rpc.MemberListRequest()
        member_list_response = await self.clusterstub.MemberList(
            member_list_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        for member in member_list_response.members:
            yield members.Member(
                member.ID,
                member.name,
                member.peerURLs,
                member.clientURLs,
                etcd_client=self,
            )

    @_handle_errors
    @_ensure_connected
    async def compact(self, revision, physical=False):
        """Compact the event history in etcd up to a given revision.

        All superseded keys with a revision less than the compaction revision
        will be removed.

        :param revision:
            Revision for the compaction operation.

        :param physical:
            If set to ``True``, the request will wait until the compaction is physically
            applied to the local database such that compacted entries are totally removed from
            the backend database.
        """
        compact_request = rpc.CompactionRequest(
            revision=revision,
            physical=physical,
        )
        await self.kvstub.Compact(
            compact_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_handle_errors
    @_ensure_connected
    async def defragment(self):
        """Defragment a member's backend database to recover storage space."""
        defrag_request = rpc.DefragmentRequest()
        await self.maintenancestub.Defragment(
            defrag_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_handle_errors
    @_ensure_connected
    async def hash(self):
        """Return the hash of the local KV state.

        :return:
            KV state hash.
        """
        hash_request = rpc.HashRequest()
        return (await self.maintenancestub.Hash(hash_request)).hash

    @_handle_errors
    @_ensure_connected
    async def create_alarm(self, member_id=0):
        """Create an alarm.

        If no member id is given, the alarm is activated for all the
        members of the cluster. Only the `no space` alarm can be raised.

        :param member_id:
            The cluster member ID to create an alarm to.
            If 0, the alarm is created for all the members of the cluster.

        :return:
            A sequence of :class:`~aetcd.client.Alarm`.
        """
        alarm_request = self._build_alarm_request('activate', member_id, 'no space')
        alarm_response = await self.maintenancestub.Alarm(
            alarm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return [
            Alarm(alarm.alarm, alarm.memberID)
            for alarm in alarm_response.alarms
        ]

    @_handle_errors
    @_ensure_connected
    async def list_alarms(self, member_id=0, alarm_type='none'):
        """List the activated alarms.

        :param member_id:
            The cluster member ID.

        :param alarm_type:
            The cluster member ID to create an alarm to.
            If 0, the alarm is created for all the members of the cluster.

        :return:
            A sequence of :class:`~aetcd.client.Alarm`.
        """
        alarm_request = self._build_alarm_request('get', member_id, alarm_type)
        alarm_response = await self.maintenancestub.Alarm(
            alarm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        for alarm in alarm_response.alarms:
            yield Alarm(alarm.alarm, alarm.memberID)

    @_handle_errors
    @_ensure_connected
    async def disarm_alarm(self, member_id=0):
        """Cancel an alarm.

        :param member_id:
            The cluster member id to cancel an alarm.
            If 0, the alarm is canceled for all the members of the cluster.

        :return: A sequence of :class:`~aetcd.client.Alarm`.
        """
        alarm_request = self._build_alarm_request('deactivate', member_id, 'no space')
        alarm_response = await self.maintenancestub.Alarm(
            alarm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return [
            Alarm(alarm.alarm, alarm.memberID)
            for alarm in alarm_response.alarms
        ]

    @_handle_errors
    @_ensure_connected
    async def snapshot(self, file_obj):
        """Take a snapshot of the database.

        :param file_obj:
            A file-like object to write the database contents in.
        """
        snapshot_request = rpc.SnapshotRequest()
        snapshot_responses = self.maintenancestub.Snapshot(
            snapshot_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        async for response in snapshot_responses:
            file_obj.write(response.blob)

    @staticmethod
    def _build_get_range_request(
        key: bytes,
        range_end: typing.Optional[bytes] = None,
        limit: typing.Optional[int] = None,
        revision: typing.Optional[int] = None,
        sort_order: typing.Optional[str] = None,
        sort_target: str = 'key',
        serializable: bool = False,
        keys_only: bool = False,
        count_only: typing.Optional[int] = None,
        min_mod_revision: typing.Optional[int] = None,
        max_mod_revision: typing.Optional[int] = None,
        min_create_revision: typing.Optional[int] = None,
        max_create_revision: typing.Optional[int] = None,
    ) -> rpc.RangeRequest:
        # TODO: Add missing request parameters: limit, revision, count_only,
        #       mid_mod_revision, max_mod_revision, min_create_revision, max_create_revision
        range_request = rpc.RangeRequest()

        range_request.key = key

        if range_end is not None:
            range_request.range_end = range_end

        if sort_order is None:
            range_request.sort_order = rpc.RangeRequest.NONE
        elif sort_order == 'ascend':
            range_request.sort_order = rpc.RangeRequest.ASCEND
        elif sort_order == 'descend':
            range_request.sort_order = rpc.RangeRequest.DESCEND
        else:
            raise ValueError(f'unknown sort order: {sort_order!r}')

        if sort_target is None or sort_target == 'key':
            range_request.sort_target = rpc.RangeRequest.KEY
        elif sort_target == 'version':
            range_request.sort_target = rpc.RangeRequest.VERSION
        elif sort_target == 'create':
            range_request.sort_target = rpc.RangeRequest.CREATE
        elif sort_target == 'mod':
            range_request.sort_target = rpc.RangeRequest.MOD
        elif sort_target == 'value':
            range_request.sort_target = rpc.RangeRequest.VALUE
        else:
            raise ValueError('sort_target must be one of "key", '
                             '"version", "create", "mod" or "value"')

        range_request.serializable = serializable
        range_request.keys_only = keys_only

        return range_request

    @staticmethod
    def _build_put_request(
        key: bytes,
        value: bytes,
        lease: typing.Optional[typing.Union[int, leases.Lease]] = None,
        prev_kv: bool = False,
        ignore_value: bool = False,
        ignore_lease: bool = False,
    ):
        # TODO: Add missing request parameters: ignore_value, ignore_lease
        put_request = rpc.PutRequest()

        put_request.key = key
        put_request.value = value
        put_request.lease = utils.lease_to_id(lease)
        put_request.prev_kv = prev_kv

        return put_request

    @staticmethod
    def _build_delete_request(
        key: bytes,
        range_end: typing.Optional[bytes] = None,
        prev_kv: bool = False,
    ):
        delete_request = rpc.DeleteRangeRequest()

        delete_request.key = key

        if range_end is not None:
            delete_request.range_end = range_end

        delete_request.prev_kv = prev_kv

        return delete_request

    def _ops_to_requests(self, ops):
        """Return a list of gRPC requests.

        Returns list from an input list of etcd3.transactions.{Put, Get,
        Delete, Txn} objects.
        """
        request_ops = []
        for op in ops:
            if isinstance(op, transactions.Put):
                request = self._build_put_request(op.key, op.value, op.lease, op.prev_kv)
                request_op = rpc.RequestOp(request_put=request)
                request_ops.append(request_op)

            elif isinstance(op, transactions.Get):
                request = self._build_get_range_request(op.key, op.range_end)
                request_op = rpc.RequestOp(request_range=request)
                request_ops.append(request_op)

            elif isinstance(op, transactions.Delete):
                request = self._build_delete_request(op.key, op.range_end, op.prev_kv)
                request_op = rpc.RequestOp(request_delete_range=request)
                request_ops.append(request_op)

            elif isinstance(op, transactions.Txn):
                compare = [c.build_message() for c in op.compare]
                success_ops = self._ops_to_requests(op.success)
                failure_ops = self._ops_to_requests(op.failure)
                request = rpc.TxnRequest(
                    compare=compare,
                    success=success_ops,
                    failure=failure_ops,
                )
                request_op = rpc.RequestOp(request_txn=request)
                request_ops.append(request_op)

            else:
                raise Exception(f'unknown request class {op.__class__!r}')

        return request_ops

    @staticmethod
    def _build_alarm_request(alarm_action, member_id, alarm_type):
        alarm_request = rpc.AlarmRequest()

        if alarm_action == 'get':
            alarm_request.action = rpc.AlarmRequest.GET
        elif alarm_action == 'activate':
            alarm_request.action = rpc.AlarmRequest.ACTIVATE
        elif alarm_action == 'deactivate':
            alarm_request.action = rpc.AlarmRequest.DEACTIVATE
        else:
            raise ValueError(f'unknown alarm action: {alarm_action!r}')

        alarm_request.memberID = member_id

        if alarm_type == 'none':
            alarm_request.alarm = rpc.NONE
        elif alarm_type == 'no space':
            alarm_request.alarm = rpc.NOSPACE
        else:
            raise ValueError(f'unknown alarm type: {alarm_type!r}')

        return alarm_request
