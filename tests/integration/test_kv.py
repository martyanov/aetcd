import base64
import contextlib
import os
import signal
import string
import subprocess
import unittest.mock

import pytest

import aetcd.exceptions
import aetcd.rpc


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


class TestClient(object):

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
