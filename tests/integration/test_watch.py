import asyncio
import base64

import pytest

import aetcd.exceptions
import aetcd.rpc
import aetcd.utils


@pytest.fixture
def etcdctl_put(etcdctl):
    async def _etcdctl_put(key, value):
        await etcdctl('put', key, value)
        result = await etcdctl('get', key)
        assert base64.b64decode(
            result['kvs'][0]['value']) == aetcd.utils.to_bytes(value)
    return _etcdctl_put


@pytest.mark.asyncio
async def test_watch_key(etcdctl, etcd, etcdctl_put):
    async def update_key():
        # Sleep to make watch can get the event
        await asyncio.sleep(3)
        await etcdctl_put('key', '0')
        await asyncio.sleep(1)
        await etcdctl_put('key', '1')
        await asyncio.sleep(1)
        await etcdctl_put('key', '2')
        await asyncio.sleep(1)
        await etcdctl_put('key', '3')
        await asyncio.sleep(1)

    t = asyncio.create_task(update_key(), name='update_key')

    change_count = 0
    w = await etcd.watch(b'key')
    async for event in w:
        assert event.kv.key == b'key'
        assert event.kv.value == aetcd.utils.to_bytes(str(change_count))

        # If cancel worked, we should not receive event 3
        assert event.kv.value != b'3'

        change_count += 1
        if change_count > 2:
            # If cancel not work, we will block in this for-loop forever
            await w.cancel()

    await t


@pytest.mark.asyncio
async def test_watch_key_with_revision_compacted(etcdctl, etcd, etcdctl_put):
    # Some data to compact
    await etcdctl('put', 'key', '0')
    result = await etcd.get(b'key')
    revision = result.mod_revision

    # Compact etcd and test watcher
    await etcd.compact(revision)

    async def update_key():
        await etcdctl_put('key', '1')
        await etcdctl_put('key', '2')
        await etcdctl_put('key', '3')

    t = asyncio.create_task(update_key(), name='update_key')

    async def watch_compacted_revision_test():
        w = await etcd.watch(b'key', start_revision=(revision - 1))

        error_raised = False
        compacted_revision = 0
        try:
            async for _ in w:
                _
        except Exception as e:
            error_raised = True
            assert isinstance(
                e,
                aetcd.exceptions.RevisionCompactedError,
            )
            compacted_revision = e.compacted_revision

        assert error_raised is True
        assert compacted_revision == revision

        change_count = 0
        w = await etcd.watch(b'key', start_revision=compacted_revision)

        async for event in w:
            assert event.kv.key == b'key'
            assert event.kv.value == aetcd.utils.to_bytes(str(change_count))

            # If cancel worked, we should not receive event 3
            assert event.kv.value != aetcd.utils.to_bytes('3')

            change_count += 1
            if change_count > 2:
                await w.cancel()

    await watch_compacted_revision_test()

    await t


@pytest.mark.asyncio
async def test_watch_key_prefix(etcdctl, etcd, etcdctl_put):
    async def update_key_prefix():
        # Sleep to make watch can get the event
        await asyncio.sleep(3)
        await etcdctl_put('/key0', '0')
        await asyncio.sleep(1)
        await etcdctl_put('/key1', '1')
        await asyncio.sleep(1)
        await etcdctl_put('/key2', '2')
        await asyncio.sleep(1)
        await etcdctl_put('/key3', '3')
        await asyncio.sleep(1)

    t = asyncio.create_task(update_key_prefix(), name='update_key_prefix')

    change_count = 0
    w = await etcd.watch_prefix(b'/key')
    async for event in w:
        assert event.kv.key == aetcd.utils.to_bytes(f'/key{change_count}')
        assert event.kv.value == aetcd.utils.to_bytes(str(change_count))

        # If cancel worked, we should not receive event 3
        assert event.kv.value != b'3'

        change_count += 1
        if change_count > 2:
            # If cancel not work, we will block in this for-loop forever
            await w.cancel()

    await t


@pytest.mark.asyncio
async def test_watch_key_once_with_put_kind(etcdctl, etcd, etcdctl_put):
    async def update_key():
        # Sleep to make watch can get the event
        await asyncio.sleep(2)
        await etcdctl_put('key', '1')
        await asyncio.sleep(1)
        await etcdctl_put('key', '2')
        await asyncio.sleep(1)

    t = asyncio.create_task(update_key(), name='update_key')

    put_count = 0
    w = await etcd.watch(b'key', kind=aetcd.EventKind.PUT, prev_kv=True)
    async for event in w:
        assert event.kv.key == b'key'

        if put_count == 0:
            assert event.prev_kv.value == b''

        if put_count == 1:
            assert event.prev_kv.value == b'1'

        put_count += 1
        if put_count > 1:
            # If cancel not work, we will block in this for-loop forever
            await w.cancel()

    assert put_count == 2

    await t


@pytest.mark.asyncio
async def test_watch_key_once_with_delete_kind(etcdctl, etcd, etcdctl_put):
    async def update_key():
        # Sleep to make watch can get the event
        await asyncio.sleep(2)
        await etcdctl_put('key', '1')
        await asyncio.sleep(1)
        await etcdctl('del', 'key')
        await asyncio.sleep(1)
        await etcdctl_put('key', '2')
        await asyncio.sleep(1)
        await etcdctl('del', 'key')
        await asyncio.sleep(1)

    t = asyncio.create_task(update_key(), name='update_key')

    del_count = 0
    w = await etcd.watch(b'key', kind=aetcd.EventKind.DELETE)
    async for event in w:
        assert event.kv.key == b'key'

        del_count += 1
        if del_count > 1:
            # If cancel not work, we will block in this for-loop forever
            await w.cancel()

    assert del_count == 2

    await t


@pytest.mark.asyncio
async def test_watch_key_prefix_once_sequential(etcd):
    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once(b'/key', 1)

    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once(b'/key', 1)

    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once(b'/key', 1)


@pytest.mark.asyncio
async def test_watch_key_ignores_global_timeout(client, etcdctl_put):
    async with client(timeout=2) as etcd:
        w = await etcd.watch(b'key')
        await asyncio.sleep(3)
        await etcdctl_put('key', '1')

        async for event in w:
            assert event.kv.value == b'1'
            break

        await w.cancel()
