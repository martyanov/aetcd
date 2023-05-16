import base64
import contextlib
import os
import signal
import string
import subprocess

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


@pytest.mark.asyncio
async def test_get_key(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')
    result = await etcd.get(b'/key')
    assert result.value == b'value'


@pytest.mark.asyncio
async def test_get_key_has_revision(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')
    result = await etcd.get(b'/key')
    assert result.header.revision > 0


@pytest.mark.skipif(
    "config.getoption('--with-cluster') is False",
    reason='ETCD cluster was not run',
)
@pytest.mark.asyncio
async def test_get_key_with_serializable(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')
    await etcdctl('put', '/key', 'updated_value')
    with _out_quorum():
        result = await etcd.get(b'/key', serializable=True)

    # Serializable read may return stale data
    assert result is None or result.value in (b'value', b'updated_value')


@pytest.mark.asyncio
async def test_get_key_unknown(etcd):
    result = await etcd.get(b'unknown')
    assert result is None


@pytest.mark.asyncio
async def test_get_prefix(etcdctl, etcd):
    for i in range(20):
        await etcdctl('put', f'/inrange{i}', 'in range')

    for i in range(5):
        await etcdctl('put', f'/notinrange{i}', 'not in range')

    results = list(await etcd.get_prefix(b'/inrange'))

    assert len(results) == 20
    for result in results:
        assert result.value == b'in range'


@pytest.mark.asyncio
async def test_get_prefix_with_keys_only(etcdctl, etcd):
    for i in range(20):
        await etcdctl('put', f'/inrange{i}', 'in range')

    for i in range(5):
        await etcdctl('put', f'/notinrange{i}', 'not in range')

    results = list(await etcd.get_prefix(b'/inrange', keys_only=True))

    assert len(results) == 20
    for result in results:
        assert result.key.startswith(b'/inrange')
        assert not result.value


@pytest.mark.asyncio
async def test_get_range(etcdctl, etcd):
    for char in string.ascii_lowercase:
        if char < 'p':
            await etcdctl('put', '/key' + char, 'in range')
        else:
            await etcdctl('put', '/key' + char, 'not in range')

    results = list(await etcd.get_range(b'/keya', b'/keyp'))

    assert len(results) == 15
    for result in results:
        assert result.value == b'in range'


@pytest.mark.asyncio
async def test_get_range_with_sort_order(etcdctl, etcd):
    def remove_prefix(key, prefix):
        return key[len(prefix):]

    initial_keys = 'abcde'
    initial_values = 'qwert'

    for k, v in zip(initial_keys, initial_values):
        await etcdctl('put', f'/key{k}', v)

    keys = b''
    for result in await etcd.get_prefix(b'/key', sort_order='ascend'):
        keys += remove_prefix(result.key, b'/key')

    assert keys == initial_keys.encode('utf-8')

    reverse_keys = b''
    for result in await etcd.get_prefix(
        b'/key',
        sort_order='descend',
    ):
        reverse_keys += remove_prefix(result.key, b'/key')

    assert reverse_keys == (''.join(reversed(initial_keys))).encode('utf-8')


@pytest.mark.asyncio
async def test_get_range_not_found(etcdctl, etcd):
    for i in range(5):
        await etcdctl('put', f'/inrange{i}', 'not in range')

    results = list(await etcd.get_prefix(b'/notinrange'))
    assert not results


@pytest.mark.asyncio
async def test_get_all(etcdctl, etcd):
    for i in range(20):
        await etcdctl('put', f'/inrange{i}', 'value')

    for i in range(5):
        await etcdctl('put', f'/notinrange{i}', 'value')

    results = list(await etcd.get_all())

    assert len(results) == 25
    for result in results:
        assert result.value == b'value'


@pytest.mark.asyncio
async def test_get_all_not_found(etcd):
    result = list(await etcd.get_all())
    assert not result


@pytest.mark.asyncio
async def test_put_key(etcdctl, etcd):
    await etcd.put(b'/key', b'value')
    result = await etcdctl('get', '/key')
    assert base64.b64decode(result['kvs'][0]['value']) == b'value'


@pytest.mark.asyncio
async def test_put_key_has_revision(etcd):
    response = await etcd.put(b'/key', b'value')
    assert response.header.revision > 0


@pytest.mark.asyncio
async def test_put_key_with_prev_kv(etcdctl, etcd):
    await etcdctl('put', '/key', 'old_value')
    result = await etcd.put(b'/key', b'value', prev_kv=True)
    assert result.prev_kv.value == b'old_value'


@pytest.mark.asyncio
async def test_delete_key(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')

    result = await etcd.get(b'/key')
    assert result.value == b'value'

    result = await etcd.delete(b'/key')
    assert result
    assert result.deleted == 1

    result = await etcd.delete(b'/key')
    assert result is None

    result = await etcd.delete(b'unknown')
    assert result is None


@pytest.mark.asyncio
async def test_delete_key_has_revision(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')

    result = await etcd.delete(b'/key')
    assert result.header.revision > 0


@pytest.mark.asyncio
async def test_delete_key_with_prev_kv(etcdctl, etcd):
    await etcdctl('put', '/key', 'old_value')
    result = await etcd.delete(
        b'/key',
        prev_kv=True,
    )
    assert result.prev_kv.value == b'old_value'
    assert result.deleted == 1


@pytest.mark.asyncio
async def test_delete_prefix_keys(etcdctl, etcd):
    await etcdctl('put', '/key1', 'value1')
    await etcdctl('put', '/key2', 'value2')

    result = await etcd.get(b'/key1')
    assert result.value == b'value1'

    result = await etcd.get(b'/key2')
    assert result.value == b'value2'

    response = await etcd.delete_prefix(b'/key')
    assert response.deleted == 2

    result = await etcd.get(b'/key1')
    assert result is None

    result = await etcd.get(b'/key2')
    assert result is None


@pytest.mark.asyncio
async def test_delete_prefix_keys_with_prev_kv(etcdctl, etcd):
    await etcdctl('put', '/key1', 'value1')
    await etcdctl('put', '/key2', 'value2')

    response = await etcd.delete_prefix(b'/key', prev_kv=True)
    assert response.deleted == 2

    kv1, kv2 = response.prev_kvs
    assert kv1.value == b'value1'
    assert kv2.value == b'value2'


@pytest.mark.asyncio
async def test_delete_range_keys(etcdctl, etcd):
    for k, v in {
        '/key\1': 'value0',
        '/key1': 'value1',
        '/key2': 'value2',
        '/key3': 'value3',
        '/key3\1': 'value30',
        '/key4': 'value4',
    }.items():
        await etcdctl('put', k, v)

    result = await etcd.get(b'/key2')
    assert result.value == b'value2'

    result = await etcd.get(b'/key4')
    assert result.value == b'value4'

    response = await etcd.delete_range(b'/key0', b'/key4')
    assert response.deleted == 4

    result = await etcd.get(b'/key\1')
    assert result.value == b'value0'

    result = await etcd.get(b'/key1')
    assert result is None

    result = await etcd.get(b'/key3\1')
    assert result is None

    result = await etcd.get(b'/key4')
    assert result.value == b'value4'


@pytest.mark.asyncio
async def test_delete_range_keys_with_prev_kv(etcdctl, etcd):
    await etcdctl('put', '/key1', 'value1')
    await etcdctl('put', '/key2', 'value2')

    response = await etcd.delete_range(b'/key1', b'/key3', prev_kv=True)
    assert response.deleted == 2

    kv1, kv2 = response.prev_kvs
    assert kv1.value == b'value1'
    assert kv2.value == b'value2'


@pytest.mark.asyncio
async def test_replace_success(etcd):
    await etcd.put(b'/key', b'value1')
    status = await etcd.replace(b'/key', b'value1', b'value2')
    result = await etcd.get(b'/key')
    assert result.value == b'value2'
    assert status is True


@pytest.mark.asyncio
async def test_replace_fail(etcd):
    await etcd.put(b'/key', b'value1')
    status = await etcd.replace(b'/key', b'value2', b'value3')
    result = await etcd.get(b'/key')
    assert result.value == b'value1'
    assert status is False


@pytest.mark.asyncio
async def test_transaction_success(etcdctl, etcd):
    await etcdctl('put', '/key', 'value')
    await etcd.transaction(
        compare=[etcd.transactions.value(b'/key') == b'value'],
        success=[etcd.transactions.put(b'/key', b'success')],
        failure=[etcd.transactions.put(b'/key', b'failure')],
    )
    result = await etcdctl('get', '/key')
    assert base64.b64decode(result['kvs'][0]['value']) == b'success'


@pytest.mark.asyncio
async def test_transaction_failure(etcdctl, etcd):
    await etcdctl('put', '/key', 'value1')
    await etcd.transaction(
        compare=[etcd.transactions.value(b'/key') == b'value2'],
        success=[etcd.transactions.put(b'/key', b'success')],
        failure=[etcd.transactions.put(b'/key', b'failure')],
    )
    result = await etcdctl('get', '/key')
    assert base64.b64decode(result['kvs'][0]['value']) == b'failure'


@pytest.mark.asyncio
async def test_nested_transactions(etcd):
    await etcd.transaction(
        compare=[],
        success=[
            etcd.transactions.put(b'/key1', b'value1'),
            etcd.transactions.txn(
                compare=[],
                success=[
                    etcd.transactions.put(b'/key2', b'value2'),
                ],
                failure=[],
            ),
        ],
        failure=[],
    )
    result = await etcd.get(b'/key1')
    assert result.value == b'value1'
    result = await etcd.get(b'/key2')
    assert result.value == b'value2'


@pytest.mark.asyncio
async def test_internal_exception_on_internal_error(mocker, etcd, rpc_error):
    kv_mock = mocker.MagicMock()
    kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.INTERNAL)
    etcd.kvstub = kv_mock

    with pytest.raises(aetcd.exceptions.InternalError):
        await etcd.get(b'key')


@pytest.mark.asyncio
async def test_connection_failure_exception_on_connection_failure(mocker, etcd, rpc_error):
    kv_mock = mocker.MagicMock()
    kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.UNAVAILABLE)
    etcd.kvstub = kv_mock

    with pytest.raises(aetcd.exceptions.ConnectionFailedError):
        await etcd.get(b'key')


@pytest.mark.asyncio
async def test_connection_timeout_exception_on_connection_timeout(mocker, etcd, rpc_error):
    kv_mock = mocker.MagicMock()
    kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)
    etcd.kvstub = kv_mock

    with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
        await etcd.get(b'key')


@pytest.mark.asyncio
async def test_grpc_exception_on_unknown_code(mocker, etcd, rpc_error):
    kv_mock = mocker.MagicMock()
    kv_mock.Range.side_effect = rpc_error(aetcd.rpc.StatusCode.DATA_LOSS)
    etcd.kvstub = kv_mock

    with pytest.raises(aetcd.exceptions.ClientError):
        await etcd.get(b'key')


@pytest.mark.asyncio
async def test_compact(etcd):
    await etcd.put(b'/foo', b'x')
    result = await etcd.get(b'/foo')
    revision = result.mod_revision

    await etcd.compact(revision)

    with pytest.raises(aetcd.ClientError):
        await etcd.compact(revision)
