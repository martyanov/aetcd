import asyncio
import functools
import inspect
import typing

from . import exceptions
from . import leases
from . import locks
from . import members
from . import rpc
from . import transactions
from . import utils
from . import watch


_EXCEPTIONS_BY_CODE = {
    rpc.StatusCode.DEADLINE_EXCEEDED: exceptions.ConnectionTimeoutError,
    rpc.StatusCode.FAILED_PRECONDITION: exceptions.PreconditionFailedError,
    rpc.StatusCode.INTERNAL: exceptions.InternalServerError,
    rpc.StatusCode.UNAVAILABLE: exceptions.ConnectionFailedError,
}


def _translate_exception(error: rpc.AioRpcError):
    exc = _EXCEPTIONS_BY_CODE.get(error.code)
    if exc is not None:
        raise exc
    raise


def _handle_errors(f):
    if inspect.iscoroutinefunction(f):
        async def handler(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except rpc.AioRpcError as e:
                _translate_exception(e)
    elif inspect.isasyncgenfunction(f):
        async def handler(*args, **kwargs):
            try:
                async for data in f(*args, **kwargs):
                    yield data
            except rpc.AioRpcError as e:
                _translate_exception(e)
    else:
        raise RuntimeError(
            f'provided function {f.__name__!r} is neither a coroutine nor an async generator')

    return functools.wraps(f)(handler)


def _ensure_connected(f):
    if inspect.iscoroutinefunction(f):
        async def handler(*args, **kwargs):
            await args[0].connect()
            return await f(*args, **kwargs)
    elif inspect.isasyncgenfunction(f):
        async def handler(*args, **kwargs):
            await args[0].connect()
            async for data in f(*args, **kwargs):
                yield data
    else:
        raise RuntimeError(
            f'provided function {f.__name__!r} is neither a coroutine nor an async generator')

    return functools.wraps(f)(handler)


class Transactions(object):
    def __init__(self):
        self.value = transactions.Value
        self.version = transactions.Version
        self.create = transactions.Create
        self.mod = transactions.Mod

        self.put = transactions.Put
        self.get = transactions.Get
        self.delete = transactions.Delete
        self.txn = transactions.Txn


class KVMetadata(object):
    def __init__(self, keyvalue, header):
        self.key = keyvalue.key
        self.create_revision = keyvalue.create_revision
        self.mod_revision = keyvalue.mod_revision
        self.version = keyvalue.version
        self.lease_id = keyvalue.lease
        self.response_header = header


class Status(object):
    def __init__(self, version, db_size, leader, raft_index, raft_term):
        self.version = version
        self.db_size = db_size
        self.leader = leader
        self.raft_index = raft_index
        self.raft_term = raft_term


class Alarm(object):
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

    :param str host:
        etcd host address, as IP address or a domain name.

    :param int port:
        etcd port number to connect to.

    :param str username:
        The name of the  user used for authentication.

    :param str password:
        Password to be used for authentication.

    :param int timeout:
        Connection timeout in secods.

    :param dict options:
        Options provided to the underlying gRPC channel.

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
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self._options = options or {}

        self._init_channel_attrs()

        self.transactions = Transactions()

    def _init_channel_attrs(self):
        # These attributes will be assigned during opening of GRPC channel
        self.channel = None
        self.metadata = None
        self.auth_stub = None
        self.kvstub = None
        self.watcher = None
        self.clusterstub = None
        self.leasestub = None
        self.maintenancestub = None

    async def connect(self):
        """Establish a connection to an etcd."""
        if self.channel:
            return

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
        self.watcher = watch.Watcher(rpc.WatchStub(self.channel), timeout=self._timeout)
        self.clusterstub = rpc.ClusterStub(self.channel)
        self.leasestub = rpc.LeaseStub(self.channel)
        self.maintenancestub = rpc.MaintenanceStub(self.channel)

    async def close(self):
        """Close all connections and free allocated resources."""
        if self.channel:
            self.watcher.close()
            await self.channel.close()
            self._init_channel_attrs()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()

    @_handle_errors
    @_ensure_connected
    async def get(self, key, serializable=False):
        """Get the value of a key from etcd.

        :param key:
            Key in etcd to get.

        :param serializable:
            Whether to allow serializable reads. This can result in stale reads.

        :return:
            A tuple of (bytes, :class:`~aetcd.client.KVMetadata`).

        Example usage:

        .. code-block:: python

            import aetcd
            client = aetcd.Client()
            await client.get('/thing/key')
        """
        range_request = self._build_get_range_request(
            key,
            serializable=serializable)
        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        if range_response.count < 1:
            return None, None
        else:
            kv = range_response.kvs.pop()
            return kv.value, KVMetadata(kv, range_response.header)

    @_handle_errors
    @_ensure_connected
    async def get_prefix(self, key_prefix, sort_order=None, sort_target='key',
                         keys_only=False):
        """Get a range of keys with a prefix.

        :param key_prefix:
            First key in range.

        :returns:
            A sequence of (bytes, :class:`~aetcd.client.KVMetadata`) tuples.
        """
        range_request = self._build_get_range_request(
            key=key_prefix,
            range_end=utils.prefix_range_end(utils.to_bytes(key_prefix)),
            sort_order=sort_order,
            sort_target=sort_target,
            keys_only=keys_only,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        if range_response.count < 1:
            return
        else:
            for kv in range_response.kvs:
                yield (kv.value, KVMetadata(kv, range_response.header))

    @_handle_errors
    @_ensure_connected
    async def get_range(self, range_start, range_end, sort_order=None,
                        sort_target='key', **kwargs):
        """Get a range of keys.

        :param range_start:
            First key in range.

        :param range_end:
            Last key in range.

        :return:
            A sequence of (bytes, :class:`~aetcd.client.KVMetadata`) tuples.
        """
        range_request = self._build_get_range_request(
            key=range_start,
            range_end=range_end,
            sort_order=sort_order,
            sort_target=sort_target,
            **kwargs,
        )

        range_response = await self.kvstub.Range(
            range_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        if range_response.count < 1:
            return
        else:
            for kv in range_response.kvs:
                yield (kv.value, KVMetadata(kv, range_response.header))

    @_handle_errors
    @_ensure_connected
    async def get_all(self, sort_order=None, sort_target='key',
                      keys_only=False):
        """Get all keys currently stored in etcd.

        :return:
            A sequence of (bytes, :class:`~aetcd.client.KVMetadata`) tuples.
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

        if range_response.count < 1:
            return
        else:
            for kv in range_response.kvs:
                yield (kv.value, KVMetadata(kv, range_response.header))

    @_handle_errors
    @_ensure_connected
    async def put(self, key, value, lease=None, prev_kv=False):
        """Save a value to etcd.

        :param key:
            Key in etcd to set.

        :param bytes value:
            Value to set key to.

        :param lease:
            Lease to associate with this key.
        :type lease:
            either :class:`~aetcd.leases.Lease`, or int (ID of lease)

        :param bool prev_kv:
            Return the previous key-value pair.

        :return:
            A response containing a header and the prev_kv.

        Example usage:

        .. code-block:: python

            import aetcd
            client = aetcd.Client()
            await client.put('/thing/key', 'hello world')
        """
        put_request = self._build_put_request(key, value, lease=lease,
                                              prev_kv=prev_kv)
        return await self.kvstub.Put(
            put_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    @_handle_errors
    @_ensure_connected
    async def replace(self, key, initial_value, new_value):
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

        :return:
            A status of transaction, ``True`` if the replace was successful,
            ``False`` otherwise.
        """
        status, _ = await self.transaction(
            compare=[
                self.transactions.value(key) == initial_value,
            ],
            success=[
                self.transactions.put(key, new_value),
            ],
            failure=[
            ],
        )

        return status

    @_handle_errors
    @_ensure_connected
    async def delete(self, key, prev_kv=False, return_response=False):
        """Delete a single key in etcd.

        :param key:
            Key in etcd to delete.

        :param bool prev_kv:
            Whether to return the deleted key-value pair.

        :param bool return_response:
            Return the full response

        :return: ``True`` if the key has been deleted when
                  ``return_response`` is ``False`` and a response containing
                  a header, the number of deleted keys and prev_kvs when
                  ``return_response`` is ``True``.
        """
        delete_request = self._build_delete_request(key, prev_kv=prev_kv)
        delete_response = await self.kvstub.DeleteRange(
            delete_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )
        if return_response:
            return delete_response
        return delete_response.deleted >= 1

    @_handle_errors
    @_ensure_connected
    async def delete_prefix(self, prefix):
        """Delete a range of keys with a prefix in etcd."""
        delete_request = self._build_delete_request(
            prefix,
            range_end=utils.prefix_range_end(utils.to_bytes(prefix)),
        )
        return await self.kvstub.DeleteRange(
            delete_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

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

        return Status(status_response.version,
                      status_response.dbSize,
                      leader,
                      status_response.raftIndex,
                      status_response.raftTerm)

    @_handle_errors
    @_ensure_connected
    async def add_watch_callback(self, *args, **kwargs):
        """Watch a key or range of keys and call a callback on every event.

        If timeout was declared during the client initialization and
        the watch cannot be created during that time the method raises
        a ``WatchTimeoutError`` exception.

        :param key:
            Key to watch.

        :param callable callback:
            Callback function.

        :return:
            A watch_id, later it could be used for cancelling watch.
        """
        try:
            return await self.watcher.add_callback(*args, **kwargs)
        except asyncio.QueueEmpty:
            raise exceptions.WatchTimeoutError

    @_handle_errors
    @_ensure_connected
    async def watch(self, key, **kwargs):
        """Watch a key.

        :param key:
            Key to watch.

        :return: tuple of ``events_iterator`` and ``cancel``.
                 Use ``events_iterator`` to get the events of key changes
                 and ``cancel`` to cancel the watch request.

        Example usage:

        .. code-block:: python

            events, cancel = await client.watch('/doot/key')
            async for event in events:
                print(event)
        """
        event_queue = asyncio.Queue()
        watch_id = await self.add_watch_callback(
            key, event_queue.put,
            **kwargs,
        )
        canceled = asyncio.Event()

        async def cancel():
            canceled.set()
            await event_queue.put(None)
            await self.cancel_watch(watch_id)

        @_handle_errors
        async def iterator():
            while not canceled.is_set():
                event = await event_queue.get()
                if event is None:
                    canceled.set()
                if isinstance(event, Exception):
                    canceled.set()
                    raise event
                if not canceled.is_set():
                    yield event

        return iterator(), cancel

    @_handle_errors
    @_ensure_connected
    async def watch_prefix(self, key_prefix, **kwargs):
        """Watches a range of keys with a prefix."""
        kwargs['range_end'] = utils.prefix_range_end(utils.to_bytes(key_prefix))
        return await self.watch(key_prefix, **kwargs)

    @_handle_errors
    @_ensure_connected
    async def watch_once(self, key, timeout=None, **kwargs):
        """Watch a key and stops after the first event.

        If the timeout was specified and event didn't arrived method
        will raise ``WatchTimeoutError`` exception.

        :param key:
            Key to watch.

        :param int timeout:
            (optional) timeout in seconds.

        :return:
            An instance of :class:`~aetcd.events.Event`.
        """
        event_queue = asyncio.Queue()

        watch_id = await self.add_watch_callback(key, event_queue.put,
                                                 **kwargs)

        try:
            return await asyncio.wait_for(event_queue.get(), timeout)
        except (asyncio.QueueEmpty, asyncio.TimeoutError):
            raise exceptions.WatchTimeoutError
        finally:
            await self.cancel_watch(watch_id)

    @_handle_errors
    @_ensure_connected
    async def watch_prefix_once(self, key_prefix, timeout=None, **kwargs):
        """Watches a range of keys with a prefix and stops after the first event.

        If the timeout was specified and event didn't arrived method
        will raise ``WatchTimeoutError`` exception.
        """
        kwargs['range_end'] = utils.prefix_range_end(utils.to_bytes(key_prefix))
        return await self.watch_once(key_prefix, timeout=timeout, **kwargs)

    @_handle_errors
    @_ensure_connected
    async def cancel_watch(self, watch_id):
        """Stop watching a key or range of keys.

        :param watch_id:
            watch_id returned by ``add_watch_callback`` method.
        """
        await self.watcher.cancel(watch_id)

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

        Example usage:

        .. code-block:: python

            await client.transaction(
                compare=[
                    client.transactions.value('/doot/testing') == 'doot',
                    client.transactions.version('/doot/testing') > 0,
                ],
                success=[
                    client.transactions.put('/doot/testing', 'success'),
                ],
                failure=[
                    client.transactions.put('/doot/testing', 'failure'),
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
            if response_type in ['response_put', 'response_delete_range',
                                 'response_txn']:
                responses.append(response)

            elif response_type == 'response_range':
                range_kvs = []
                for kv in response.response_range.kvs:
                    range_kvs.append((kv.value,
                                      KVMetadata(kv, txn_response.header)))

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
        return leases.Lease(lease_id=lease_grant_response.ID,
                            ttl=lease_grant_response.TTL,
                            etcd_client=self)

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
        return await self.leasestub.LeaseKeepAlive(
            [rpc.LeaseKeepAliveRequest(ID=lease_id)],
            timeout=self._timeout,
            metadata=self.metadata)

    @_handle_errors
    @_ensure_connected
    async def get_lease_info(self, lease_id, *, keys=True):
        # only available in etcd v3.1.0 and later
        ttl_request = rpc.LeaseTimeToLiveRequest(
            ID=lease_id,
            keys=keys,
        )
        return await self.leasestub.LeaseTimeToLive(
            ttl_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

    def lock(self, name, ttl=60):
        """Create a new lock.

        :param name:
            Name of the lock.

        :param int ttl:
            Length of time for the lock to live for in seconds. The
            lock will be released after this time elapses, unless refreshed.

        :return:
            A new lock, an instance of :class:`~aetcd.locks.Lock`.
        """
        return locks.Lock(name, ttl=ttl, etcd_client=self)

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
        alarm_request = self._build_alarm_request('activate',
                                                  member_id,
                                                  'no space')
        alarm_response = await self.maintenancestub.Alarm(
            alarm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return [Alarm(alarm.alarm, alarm.memberID)
                for alarm in alarm_response.alarms]

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
        alarm_request = self._build_alarm_request('get',
                                                  member_id,
                                                  alarm_type)
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
        alarm_request = self._build_alarm_request('deactivate',
                                                  member_id,
                                                  'no space')
        alarm_response = await self.maintenancestub.Alarm(
            alarm_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        return [Alarm(alarm.alarm, alarm.memberID)
                for alarm in alarm_response.alarms]

    @_handle_errors
    @_ensure_connected
    async def snapshot(self, file_obj):
        """Take a snapshot of the database.

        :param file_obj:
            A file-like object to write the database contents in.
        """
        snapshot_request = rpc.SnapshotRequest()
        snapshot_responses = await self.maintenancestub.Snapshot(
            snapshot_request,
            timeout=self._timeout,
            metadata=self.metadata,
        )

        for response in snapshot_responses:
            file_obj.write(response.blob)

    @staticmethod
    def _build_get_range_request(key,
                                 range_end=None,
                                 limit=None,
                                 revision=None,
                                 sort_order=None,
                                 sort_target='key',
                                 serializable=False,
                                 keys_only=False,
                                 count_only=None,
                                 min_mod_revision=None,
                                 max_mod_revision=None,
                                 min_create_revision=None,
                                 max_create_revision=None):
        range_request = rpc.RangeRequest()
        range_request.key = utils.to_bytes(key)
        range_request.keys_only = keys_only
        if range_end is not None:
            range_request.range_end = utils.to_bytes(range_end)

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

        return range_request

    @staticmethod
    def _build_put_request(key, value, lease=None, prev_kv=False):
        put_request = rpc.PutRequest()
        put_request.key = utils.to_bytes(key)
        put_request.value = utils.to_bytes(value)
        put_request.lease = utils.lease_to_id(lease)
        put_request.prev_kv = prev_kv

        return put_request

    @staticmethod
    def _build_delete_request(key,
                              range_end=None,
                              prev_kv=False):
        delete_request = rpc.DeleteRangeRequest()
        delete_request.key = utils.to_bytes(key)
        delete_request.prev_kv = prev_kv

        if range_end is not None:
            delete_request.range_end = utils.to_bytes(range_end)

        return delete_request

    def _ops_to_requests(self, ops):
        """Return a list of gRPC requests.

        Returns list from an input list of etcd3.transactions.{Put, Get,
        Delete, Txn} objects.
        """
        request_ops = []
        for op in ops:
            if isinstance(op, transactions.Put):
                request = self._build_put_request(op.key, op.value,
                                                  op.lease, op.prev_kv)
                request_op = rpc.RequestOp(request_put=request)
                request_ops.append(request_op)

            elif isinstance(op, transactions.Get):
                request = self._build_get_range_request(op.key, op.range_end)
                request_op = rpc.RequestOp(request_range=request)
                request_ops.append(request_op)

            elif isinstance(op, transactions.Delete):
                request = self._build_delete_request(op.key, op.range_end,
                                                     op.prev_kv)
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
