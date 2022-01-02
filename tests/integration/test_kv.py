import asyncio
import base64
import contextlib
import os
import signal
import string
import subprocess
import tempfile
import threading
import time
import unittest.mock
import urllib.parse

import pytest
import tenacity

import aetcd.exceptions
import aetcd.rpc
import aetcd.utils as utils


@contextlib.contextmanager
def _out_quorum():
    pids = subprocess.check_output(['pgrep', '-f', '--', '--name pifpaf[12]'])
    pids = [int(pid.strip()) for pid in pids.splitlines()]
    try:
        for pid in pids:
            os.kill(pid, signal.SIGSTOP)
        yield
    finally:
        for pid in pids:
            os.kill(pid, signal.SIGCONT)


class TestEtcd3:

    @pytest.fixture
    async def etcd(self, etcdctl):
        endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
        timeout = 5
        if endpoint:
            url = urllib.parse.urlparse(endpoint)
            with aetcd.Client(
                host=url.hostname,
                port=url.port,
                timeout=timeout,
            ) as client:
                yield client
        else:
            async with aetcd.Client() as client:
                yield client

        @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3))
        def delete_keys_definitely():
            # clean up after fixture goes out of scope
            etcdctl('del', '--prefix', '/')
            out = etcdctl('get', '--prefix', '/')
            assert 'kvs' not in out

        delete_keys_definitely()

    @pytest.mark.asyncio
    async def test_get_unknown_key(self, etcd):
        result = await etcd.get(b'probably-invalid-key')
        assert result is None

    @pytest.mark.asyncio
    async def test_get_key(self, etcdctl, etcd, string='xxx'):
        etcdctl('put', '/doot/a_key', string)
        result = await etcd.get(b'/doot/a_key')
        assert result.value == string.encode('utf-8')

    @pytest.mark.asyncio
    async def test_get_random_key(self, etcdctl, etcd, string='xxxx'):
        etcdctl('put', '/doot/' + string, 'dootdoot')
        result = await etcd.get(b'/doot/' + string.encode('utf-8'))
        assert result.value == b'dootdoot'

    @pytest.mark.asyncio
    async def test_get_have_cluster_revision(self, etcdctl, etcd, string='xxx'):
        etcdctl('put', '/doot/' + string, 'dootdoot')
        result = await etcd.get(b'/doot/' + string.encode('utf-8'))
        assert result.header.revision > 0

    @pytest.mark.asyncio
    async def test_put_key(self, etcdctl, etcd, string='xxx'):
        await etcd.put(b'/doot/put_1', string.encode('utf-8'))
        out = etcdctl('get', '/doot/put_1')
        assert base64.b64decode(out['kvs'][0]['value']) == string.encode('utf-8')

    @pytest.mark.asyncio
    async def test_get_key_serializable(self, etcdctl, etcd, key='foo', string='xxx'):
        etcdctl('put', '/doot/' + key, string)
        with _out_quorum():
            result = await etcd.get(b'/doot/' + key.encode('utf-8'), serializable=True)
        assert result.value == string.encode('utf-8')

    @pytest.mark.asyncio
    async def test_put_has_cluster_revision(self, etcd):
        response = await etcd.put(b'/doot/put_1', b'xxx')
        assert response.header.revision > 0

    @pytest.mark.asyncio
    async def test_put_has_prev_kv(self, etcdctl, etcd):
        etcdctl('put', '/doot/put_1', 'old_value')
        response = await etcd.put(b'/doot/put_1', b'xxxx', prev_kv=True)
        assert response.prev_kv.value == b'old_value'

    @pytest.mark.asyncio
    async def test_delete_key(self, etcdctl, etcd):
        etcdctl('put', '/doot/delete_this', 'delete pls')

        result = await etcd.get(b'/doot/delete_this')
        assert result.value == b'delete pls'

        result = await etcd.delete(b'/doot/delete_this')
        assert result

        result = await etcd.delete(b'/doot/delete_this')
        assert not result

        result = await etcd.delete(b'/doot/not_here_dude')
        assert not result

    @pytest.mark.asyncio
    async def test_delete_has_cluster_revision(self, etcd):
        result = await etcd.delete(b'/doot/delete_this')
        assert result.header.revision > 0

    @pytest.mark.asyncio
    async def test_delete_has_prev_kv(self, etcdctl, etcd):
        etcdctl('put', '/doot/delete_this', 'old_value')
        result = await etcd.delete(
            b'/doot/delete_this',
            prev_kv=True,
        )
        assert result.prev_kv.value == b'old_value'
        assert result.deleted == 1

    @pytest.mark.asyncio
    async def test_delete_keys_with_prefix(self, etcdctl, etcd):
        etcdctl('put', '/foo/1', 'bar')
        etcdctl('put', '/foo/2', 'baz')

        result = await etcd.get(b'/foo/1')
        assert result.value == b'bar'

        result = await etcd.get(b'/foo/2')
        assert result.value == b'baz'

        response = await etcd.delete_prefix(b'/foo')
        assert response.deleted == 2

        result = await etcd.get(b'/foo/1')
        assert result is None

        result = await etcd.get(b'/foo/2')
        assert result is None

    @pytest.mark.asyncio
    async def test_watch_key(self, etcdctl, etcd):
        def update_etcd(v):
            etcdctl('put', '/doot/watch', v)
            out = etcdctl('get', '/doot/watch')
            assert base64.b64decode(out['kvs'][0]['value']) == utils.to_bytes(v)

        def update_key():
            # sleep to make watch can get the event
            time.sleep(3)
            update_etcd('0')
            time.sleep(1)
            update_etcd('1')
            time.sleep(1)
            update_etcd('2')
            time.sleep(1)
            update_etcd('3')
            time.sleep(1)

        t = threading.Thread(name='update_key', target=update_key)
        t.start()

        change_count = 0
        events_iterator, cancel = await etcd.watch(b'/doot/watch')
        async for event in events_iterator:
            assert event.key == b'/doot/watch'
            assert event.value == utils.to_bytes(str(change_count))

            # if cancel worked, we should not receive event 3
            assert event.value != utils.to_bytes('3')

            change_count += 1
            if change_count > 2:
                # if cancel not work, we will block in this for-loop forever
                await cancel()

        t.join()

    @pytest.mark.asyncio
    async def test_watch_key_with_revision_compacted(self, etcdctl, etcd):
        etcdctl('put', '/watchcompation', '0')  # Some data to compact
        result = await etcd.get(b'/watchcompation')
        revision = result.mod_revision

        # Compact etcd and test watcher
        await etcd.compact(revision)

        def update_etcd(v):
            etcdctl('put', '/watchcompation', v)
            out = etcdctl('get', '/watchcompation')
            assert base64.b64decode(out['kvs'][0]['value']) == utils.to_bytes(v)

        def update_key():
            update_etcd('1')
            update_etcd('2')
            update_etcd('3')

        t = threading.Thread(name='update_key', target=update_key)
        t.start()

        async def watch_compacted_revision_test():
            events_iterator, cancel = await etcd.watch(
                b'/watchcompation', start_revision=(revision - 1))

            error_raised = False
            compacted_revision = 0
            try:
                await events_iterator.__anext__()
            except Exception as err:
                error_raised = True
                assert isinstance(err,
                                  aetcd.exceptions.RevisionCompactedError)
                compacted_revision = err.compacted_revision

            assert error_raised is True
            assert compacted_revision == revision

            change_count = 0
            events_iterator, cancel = await etcd.watch(
                b'/watchcompation', start_revision=compacted_revision)
            async for event in events_iterator:
                assert event.key == b'/watchcompation'
                assert event.value == utils.to_bytes(str(change_count))

                # if cancel worked, we should not receive event 3
                assert event.value != utils.to_bytes('3')

                change_count += 1
                if change_count > 2:
                    await cancel()

        await watch_compacted_revision_test()

        t.join()

    @pytest.mark.asyncio
    async def test_watch_exception_during_watch(self, etcd, rpc_error):
        await etcd.connect()

        async def pass_exception_to_callback(callback):
            await asyncio.sleep(1)
            ex = rpc_error(aetcd.rpc.StatusCode.UNAVAILABLE)
            await callback(ex)

        task = None

        async def add_callback_mock(*args, **kwargs):
            nonlocal task
            callback = args[1]
            task = asyncio.get_event_loop().create_task(
                pass_exception_to_callback(callback))
            return 1

        watcher_mock = unittest.mock.MagicMock()
        watcher_mock.add_callback = add_callback_mock
        etcd.watcher = watcher_mock

        events_iterator, cancel = await etcd.watch('foo')

        with pytest.raises(aetcd.exceptions.ConnectionFailedError):
            async for _ in events_iterator:
                pass

        await task

    @pytest.mark.skip('broken implementation')
    @pytest.mark.asyncio
    async def test_watch_timeout_on_establishment(self):
        async with aetcd.Client(timeout=3) as foo_etcd:
            @contextlib.asynccontextmanager
            async def slow_watch_mock(*args, **kwargs):
                await asyncio.sleep(40)
                yield 'foo'

            foo_etcd.watcher._watch_stub.Watch.open = slow_watch_mock  # noqa

            with pytest.raises(aetcd.exceptions.WatchTimeoutError):
                events_iterator, cancel = await foo_etcd.watch('foo')
                async for _ in events_iterator:
                    pass

    @pytest.mark.asyncio
    async def test_watch_prefix(self, etcdctl, etcd):
        def update_etcd(v):
            etcdctl('put', '/doot/watch/prefix/' + v, v)
            out = etcdctl('get', '/doot/watch/prefix/' + v)
            assert base64.b64decode(out['kvs'][0]['value']) == utils.to_bytes(v)

        def update_key():
            # sleep to make watch can get the event
            time.sleep(3)
            update_etcd('0')
            time.sleep(1)
            update_etcd('1')
            time.sleep(1)
            update_etcd('2')
            time.sleep(1)
            update_etcd('3')
            time.sleep(1)

        t = threading.Thread(name='update_key_prefix', target=update_key)
        t.start()

        change_count = 0
        events_iterator, cancel = await etcd.watch_prefix(
            '/doot/watch/prefix/')
        async for event in events_iterator:
            assert event.key == utils.to_bytes(f'/doot/watch/prefix/{change_count}')
            assert event.value == utils.to_bytes(str(change_count))

            # if cancel worked, we should not receive event 3
            assert event.value != utils.to_bytes('3')

            change_count += 1
            if change_count > 2:
                # if cancel not work, we will block in this for-loop forever
                await cancel()

        t.join()

    @pytest.mark.asyncio
    async def test_sequential_watch_prefix_once(self, etcd):
        try:
            await etcd.watch_prefix_once('/doot/', 1)
        except aetcd.exceptions.WatchTimeoutError:
            print('timeout1')
            pass
        try:
            await etcd.watch_prefix_once('/doot/', 1)
        except aetcd.exceptions.WatchTimeoutError:
            print('timeout2')
            pass
        try:
            await etcd.watch_prefix_once('/doot/', 1)
        except aetcd.exceptions.WatchTimeoutError:
            print('timeout3')
            pass

    @pytest.mark.asyncio
    async def test_transaction_success(self, etcdctl, etcd):
        etcdctl('put', '/doot/txn', 'dootdoot')
        await etcd.transaction(
            compare=[etcd.transactions.value(b'/doot/txn') == b'dootdoot'],
            success=[etcd.transactions.put(b'/doot/txn', b'success')],
            failure=[etcd.transactions.put(b'/doot/txn', b'failure')],
        )
        out = etcdctl('get', '/doot/txn')
        assert base64.b64decode(out['kvs'][0]['value']) == b'success'

    @pytest.mark.asyncio
    async def test_transaction_failure(self, etcdctl, etcd):
        etcdctl('put', '/doot/txn', 'notdootdoot')
        await etcd.transaction(
            compare=[etcd.transactions.value(b'/doot/txn') == b'dootdoot'],
            success=[etcd.transactions.put(b'/doot/txn', b'success')],
            failure=[etcd.transactions.put(b'/doot/txn', b'failure')],
        )
        out = etcdctl('get', '/doot/txn')
        assert base64.b64decode(out['kvs'][0]['value']) == b'failure'

    def test_ops_to_requests(self, etcd):
        with pytest.raises(Exception):
            etcd._ops_to_requests(['not_transaction_type'])
        with pytest.raises(TypeError):
            etcd._ops_to_requests(0)

    @pytest.mark.asyncio
    async def test_nested_transactions(self, etcd):
        await etcd.transaction(
            compare=[],
            success=[etcd.transactions.put(b'/doot/txn1', b'1'),
                     etcd.transactions.txn(
                         compare=[],
                         success=[etcd.transactions.put(b'/doot/txn2', b'2')],
                         failure=[])],
            failure=[],
        )
        result = await etcd.get(b'/doot/txn1')
        assert result.value == b'1'
        result = await etcd.get(b'/doot/txn2')
        assert result.value == b'2'

    @pytest.mark.asyncio
    async def test_replace_success(self, etcd):
        await etcd.put(b'/doot/thing', b'toot')
        status = await etcd.replace(b'/doot/thing', b'toot', b'doot')
        result = await etcd.get(b'/doot/thing')
        assert result.value == b'doot'
        assert status is True

    @pytest.mark.asyncio
    async def test_replace_fail(self, etcd):
        await etcd.put(b'/doot/thing', b'boot')
        status = await etcd.replace(b'/doot/thing', b'toot', b'doot')
        result = await etcd.get(b'/doot/thing')
        assert result.value == b'boot'
        assert status is False

    @pytest.mark.asyncio
    async def test_get_prefix(self, etcdctl, etcd):
        for i in range(20):
            etcdctl('put', f'/doot/range{i}', 'i am a range')

        for i in range(5):
            etcdctl('put', f'/doot/notrange{i}', 'i am a not range')

        results = list(await etcd.get_prefix(b'/doot/range'))
        assert len(results) == 20
        for result in results:
            assert result.value == b'i am a range'

    @pytest.mark.asyncio
    async def test_get_prefix_keys_only(self, etcdctl, etcd):
        for i in range(20):
            etcdctl('put', f'/doot/range{i}', 'i am a range')

        for i in range(5):
            etcdctl('put', f'/doot/notrange{i}', 'i am a not range')

        results = list(await etcd.get_prefix(b'/doot/range', keys_only=True))
        assert len(results) == 20
        for result in results:
            assert result.key.startswith(b'/doot/range')
            assert not result.value

    @pytest.mark.asyncio
    async def test_get_range(self, etcdctl, etcd):
        for char in string.ascii_lowercase:
            if char < 'p':
                etcdctl('put', '/doot/' + char, 'i am in range')
            else:
                etcdctl('put', '/doot/' + char, 'i am not in range')

        results = list(await etcd.get_range(b'/doot/a', b'/doot/p'))
        assert len(results) == 15
        for result in results:
            assert result.value == b'i am in range'

    @pytest.mark.asyncio
    async def test_all_not_found_error(self, etcd):
        result = list(await etcd.get_all())
        assert not result

    @pytest.mark.asyncio
    async def test_range_not_found_error(self, etcdctl, etcd):
        for i in range(5):
            etcdctl('put', f'/doot/notrange{i}', 'i am a not range')

        results = list(await etcd.get_prefix(b'/doot/range'))
        assert not results

    @pytest.mark.asyncio
    async def test_get_all(self, etcdctl, etcd):
        for i in range(20):
            etcdctl('put', f'/doot/range{i}', 'i am in all')

        for i in range(5):
            etcdctl('put', f'/doot/notrange{i}', 'i am in all')
        results = list(await etcd.get_all())
        assert len(results) == 25
        for result in results:
            assert result.value == b'i am in all'

    @pytest.mark.asyncio
    async def test_sort_order(self, etcdctl, etcd):
        def remove_prefix(string, prefix):
            return string[len(prefix):]

        initial_keys = 'abcde'
        initial_values = 'qwert'

        for k, v in zip(initial_keys, initial_values):
            etcdctl('put', f'/doot/{k}', v)

        keys = ''
        for result in await etcd.get_prefix(b'/doot', sort_order='ascend'):
            keys += remove_prefix(result.key.decode('utf-8'), '/doot/')

        assert keys == initial_keys

        reverse_keys = ''
        for result in await etcd.get_prefix(
            b'/doot',
            sort_order='descend',
        ):
            reverse_keys += remove_prefix(result.key.decode('utf-8'), '/doot/')

        assert reverse_keys == ''.join(reversed(initial_keys))

    @pytest.mark.asyncio
    async def test_lease_grant(self, etcd):
        lease = await etcd.lease(1)

        assert isinstance(lease.ttl, int)
        assert isinstance(lease.id, int)

    @pytest.mark.asyncio
    async def test_lease_revoke(self, etcd):
        lease = await etcd.lease(1)
        await lease.revoke()

    @pytest.mark.asyncio
    async def test_lease_keys_empty(self, etcd):
        lease = await etcd.lease(1)
        assert (await lease.keys()) == []

    @pytest.mark.asyncio
    async def test_lease_single_key(self, etcd):
        lease = await etcd.lease(1)
        await etcd.put(b'/doot/lease_test', b'this is a lease', lease=lease)
        assert (await lease.keys()) == [b'/doot/lease_test']

    @pytest.mark.asyncio
    async def test_lease_expire(self, etcd):
        key = b'/doot/lease_test_expire'
        lease = await etcd.lease(1)
        await etcd.put(key, b'this is a lease', lease=lease)
        assert (await lease.keys()) == [utils.to_bytes(key)]
        result = await etcd.get(key)
        assert result.value == b'this is a lease'
        assert (await lease.remaining_ttl()) <= (await lease.granted_ttl())

        # wait for the lease to expire
        await asyncio.sleep((await lease.granted_ttl()) + 2)
        result = await etcd.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_member_list(self, etcd):
        assert len([m async for m in etcd.members()]) == 3
        async for member in etcd.members():
            assert member.name.startswith('pifpaf')
            for peer_url in member.peer_urls:
                assert peer_url.startswith('http://')
            for client_url in member.client_urls:
                assert client_url.startswith('http://')
            assert isinstance(member.id, int) is True

    @pytest.mark.asyncio
    async def test_lock_acquire(self, etcd):
        lock = etcd.lock(b'lock-1', ttl=10)
        assert (await lock.acquire()) is True
        assert (await etcd.get(lock.key)).value is not None
        assert (await lock.acquire(timeout=0)) is False
        assert (await lock.acquire(timeout=1)) is False

    @pytest.mark.asyncio
    async def test_lock_release(self, etcd):
        lock = etcd.lock(b'lock-2', ttl=10)
        assert (await lock.acquire()) is True
        assert (await etcd.get(lock.key)).value is not None
        assert (await lock.release()) is True
        result = await etcd.get(lock.key)
        assert result is None
        assert (await lock.acquire()) is True
        assert (await lock.release()) is True
        assert (await lock.acquire(timeout=None)) is True

    @pytest.mark.asyncio
    async def test_lock_expire(self, etcd):
        lock = etcd.lock(b'lock-3', ttl=3)
        assert (await lock.acquire()) is True
        assert (await etcd.get(lock.key)).value is not None
        # wait for the lease to expire
        await asyncio.sleep(9)
        result = await etcd.get(lock.key)
        assert result is None

    @pytest.mark.asyncio
    async def test_lock_refresh(self, etcd):
        lock = etcd.lock(b'lock-4', ttl=3)
        assert (await lock.acquire()) is True
        assert (await etcd.get(lock.key)).value is not None
        # sleep for the same total time as test_lock_expire, but refresh each
        # second
        for _ in range(9):
            await asyncio.sleep(1)
            await lock.refresh()

        assert (await etcd.get(lock.key)).value is not None

    @pytest.mark.asyncio
    async def test_lock_is_acquired(self, etcd):
        lock1 = etcd.lock(b'lock-5', ttl=2)
        assert (await lock1.is_acquired()) is False

        lock2 = etcd.lock(b'lock-5', ttl=2)
        await lock2.acquire()
        assert (await lock2.is_acquired()) is True
        await lock2.release()

        lock3 = etcd.lock(b'lock-5', ttl=2)
        await lock3.acquire()
        assert (await lock3.is_acquired()) is True
        assert (await lock2.is_acquired()) is False

    @pytest.mark.asyncio
    async def test_lock_context_manager(self, etcd):
        async with etcd.lock(b'lock-6', ttl=2) as lock:
            assert (await lock.is_acquired()) is True
        assert (await lock.is_acquired()) is False

    @pytest.mark.asyncio
    async def test_lock_contended(self, etcd):
        lock1 = etcd.lock(b'lock-7', ttl=2)
        await lock1.acquire()
        lock2 = etcd.lock(b'lock-7', ttl=2)
        await lock2.acquire()
        assert (await lock1.is_acquired()) is False
        assert (await lock2.is_acquired()) is True

    @pytest.mark.asyncio
    async def test_lock_double_acquire_release(self, etcd):
        lock = etcd.lock(b'lock-8', ttl=10)
        assert (await lock.acquire(0)) is True
        assert (await lock.acquire(0)) is False
        assert (await lock.release()) is True

    @pytest.mark.asyncio
    async def test_lock_acquire_none(self, etcd):
        lock = etcd.lock(b'lock-9', ttl=10)
        assert (await lock.acquire(None)) is True
        # This will succeed after 10 seconds since the TTL will expire and the
        # lock is not refreshed
        assert (await lock.acquire(None)) is True

    @pytest.mark.asyncio
    async def test_internal_exception_on_internal_error(self, etcd, rpc_error):
        kv_mock = unittest.mock.MagicMock()
        kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.INTERNAL)
        etcd.kvstub = kv_mock

        with pytest.raises(aetcd.exceptions.InternalServerError):
            await etcd.get(b'key')

    @pytest.mark.asyncio
    async def test_connection_failure_exception_on_connection_failure(self, etcd, rpc_error):
        kv_mock = unittest.mock.MagicMock()
        kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.UNAVAILABLE)
        etcd.kvstub = kv_mock

        with pytest.raises(aetcd.exceptions.ConnectionFailedError):
            await etcd.get(b'key')

    @pytest.mark.asyncio
    async def test_connection_timeout_exception_on_connection_timeout(self, etcd, rpc_error):
        kv_mock = unittest.mock.MagicMock()
        kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)
        etcd.kvstub = kv_mock

        with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
            await etcd.get(b'key')

    @pytest.mark.asyncio
    async def test_grpc_exception_on_unknown_code(self, etcd, rpc_error):
        kv_mock = unittest.mock.MagicMock()
        kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.DATA_LOSS)
        etcd.kvstub = kv_mock

        with pytest.raises(aetcd.exceptions.ClientError):
            await etcd.get(b'key')

    @pytest.mark.asyncio
    async def test_status_member(self, etcd):
        status = await etcd.status()

        assert isinstance(status.leader, aetcd.members.Member) is True
        assert status.leader.id in [m.id async for m in etcd.members()]

    @pytest.mark.asyncio
    async def test_hash(self, etcd):
        assert isinstance((await etcd.hash()), int)

    @pytest.mark.asyncio
    async def test_snapshot(self, etcdctl, etcd):
        with tempfile.NamedTemporaryFile() as f:
            await etcd.snapshot(f)
            f.flush()

            etcdctl('snapshot', 'status', f.name)


class TestAlarms(object):
    @pytest.fixture
    async def etcd(self):
        etcd = aetcd.Client()
        yield etcd
        await etcd.disarm_alarm()
        async for m in etcd.members():
            if m.active_alarms:
                await etcd.disarm_alarm(m.id)

    @pytest.mark.asyncio
    async def test_create_alarm_all_members(self, etcd):
        alarms = await etcd.create_alarm()

        assert len(alarms) == 1
        assert alarms[0].member_id == 0
        assert alarms[0].alarm_type == aetcd.rpc.NOSPACE

    @pytest.mark.asyncio
    async def test_create_alarm_specific_member(self, etcd):
        members = [m async for m in etcd.members()]
        a_member = members[0]

        alarms = await etcd.create_alarm(member_id=a_member.id)

        assert len(alarms) == 1
        assert alarms[0].member_id == a_member.id
        assert alarms[0].alarm_type == aetcd.rpc.NOSPACE

    @pytest.mark.asyncio
    async def test_list_alarms(self, etcd):
        members = [m async for m in etcd.members()]
        a_member = members[0]
        await etcd.create_alarm()
        await etcd.create_alarm(member_id=a_member.id)
        possible_member_ids = [0, a_member.id]

        alarms = [a async for a in etcd.list_alarms()]

        assert len(alarms) == 2
        for alarm in alarms:
            possible_member_ids.remove(alarm.member_id)
            assert alarm.alarm_type == aetcd.rpc.NOSPACE

        assert possible_member_ids == []

    @pytest.mark.asyncio
    async def test_disarm_alarm(self, etcd):
        await etcd.create_alarm()
        assert len([a async for a in etcd.list_alarms()]) == 1

        await etcd.disarm_alarm()
        assert len([a async for a in etcd.list_alarms()]) == 0


class TestUtils(object):
    def test_prefix_range_end(self):
        assert aetcd.utils.prefix_range_end(b'foo') == b'fop'

    def test_to_bytes(self):
        assert isinstance(aetcd.utils.to_bytes(b'doot'), bytes) is True
        assert isinstance(aetcd.utils.to_bytes('doot'), bytes) is True
        assert aetcd.utils.to_bytes(b'doot') == b'doot'
        assert aetcd.utils.to_bytes('doot') == b'doot'


class TestClient(object):
    @pytest.fixture
    def etcd(self):
        yield aetcd.Client()

    def test_sort_target(self, etcd):
        key = 'key'.encode('utf-8')
        sort_target = {
            None: aetcd.rpc.RangeRequest.KEY,
            'key': aetcd.rpc.RangeRequest.KEY,
            'version': aetcd.rpc.RangeRequest.VERSION,
            'create': aetcd.rpc.RangeRequest.CREATE,
            'mod': aetcd.rpc.RangeRequest.MOD,
            'value': aetcd.rpc.RangeRequest.VALUE,
        }

        for input, expected in sort_target.items():
            range_request = etcd._build_get_range_request(key,
                                                          sort_target=input)
            assert range_request.sort_target == expected
        with pytest.raises(ValueError):
            etcd._build_get_range_request(key, sort_target='feelsbadman')

    def test_sort_order(self, etcd):
        key = 'key'.encode('utf-8')
        sort_target = {
            None: aetcd.rpc.RangeRequest.NONE,
            'ascend': aetcd.rpc.RangeRequest.ASCEND,
            'descend': aetcd.rpc.RangeRequest.DESCEND,
        }

        for input, expected in sort_target.items():
            range_request = etcd._build_get_range_request(key,
                                                          sort_order=input)
            assert range_request.sort_order == expected
        with pytest.raises(ValueError):
            etcd._build_get_range_request(key, sort_order='feelsbadman')

    @pytest.mark.asyncio
    async def test_compact(self, etcd):
        await etcd.put(b'/foo', b'x')
        result = await etcd.get(b'/foo')
        revision = result.mod_revision
        await etcd.compact(revision)
        with pytest.raises(aetcd.ClientError):
            await etcd.compact(revision)

    @pytest.mark.asyncio
    async def test_username_password_auth(self):
        with self._enabled_auth_in_etcd():
            # Create a client using username and password auth
            client = aetcd.Client(
                username='root',
                password='pwd',
            )
            await client.get(b'probably-invalid-key')

    def test_username_or_password_auth_raises_exception(self):
        with pytest.raises(Exception, match='both username and password'):
            aetcd.Client(username='usr')

        with pytest.raises(Exception, match='both username and password'):
            aetcd.Client(password='pwd')

    @staticmethod
    @contextlib.contextmanager
    def _enabled_auth_in_etcd():
        subprocess.call(['etcdctl', '-w', 'json', 'user', 'add', 'root:pwd'])
        subprocess.call(['etcdctl', 'auth', 'enable'])
        try:
            yield
        finally:
            subprocess.call(['etcdctl',
                             '-w', 'json', '--user', 'root:pwd',
                             'auth', 'disable'])
            subprocess.call(['etcdctl', 'user', 'delete', 'root'])
            subprocess.call(['etcdctl', 'role', 'delete', 'root'])


class TestCompares(object):

    def test_compare_version(self):
        key = 'key'
        tx = aetcd.Transactions()

        version_compare = tx.version(key) == 1
        assert version_compare.op == aetcd.rpc.Compare.EQUAL

        version_compare = tx.version(key) != 2
        assert version_compare.op == aetcd.rpc.Compare.NOT_EQUAL

        version_compare = tx.version(key) < 91
        assert version_compare.op == aetcd.rpc.Compare.LESS

        version_compare = tx.version(key) > 92
        assert version_compare.op == aetcd.rpc.Compare.GREATER
        assert version_compare.build_message().target == aetcd.rpc.Compare.VERSION

    def test_compare_value(self):
        key = 'key'
        tx = aetcd.Transactions()

        value_compare = tx.value(key) == 'b'
        assert value_compare.op == aetcd.rpc.Compare.EQUAL

        value_compare = tx.value(key) != 'b'
        assert value_compare.op == aetcd.rpc.Compare.NOT_EQUAL

        value_compare = tx.value(key) < 'b'
        assert value_compare.op == aetcd.rpc.Compare.LESS

        value_compare = tx.value(key) > 'b'
        assert value_compare.op == aetcd.rpc.Compare.GREATER
        assert value_compare.build_message().target == aetcd.rpc.Compare.VALUE

    def test_compare_mod(self):
        key = 'key'
        tx = aetcd.Transactions()

        mod_compare = tx.mod(key) == -100
        assert mod_compare.op == aetcd.rpc.Compare.EQUAL

        mod_compare = tx.mod(key) != -100
        assert mod_compare.op == aetcd.rpc.Compare.NOT_EQUAL

        mod_compare = tx.mod(key) < 19
        assert mod_compare.op == aetcd.rpc.Compare.LESS

        mod_compare = tx.mod(key) > 21
        assert mod_compare.op == aetcd.rpc.Compare.GREATER
        assert mod_compare.build_message().target == aetcd.rpc.Compare.MOD

    def test_compare_create(self):
        key = 'key'
        tx = aetcd.Transactions()

        create_compare = tx.create(key) == 10
        assert create_compare.op == aetcd.rpc.Compare.EQUAL

        create_compare = tx.create(key) != 10
        assert create_compare.op == aetcd.rpc.Compare.NOT_EQUAL

        create_compare = tx.create(key) < 155
        assert create_compare.op == aetcd.rpc.Compare.LESS

        create_compare = tx.create(key) > -12
        assert create_compare.op == aetcd.rpc.Compare.GREATER
        assert create_compare.build_message().target == aetcd.rpc.Compare.CREATE
