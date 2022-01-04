import asyncio
import base64
import threading
import time

import pytest

import aetcd.exceptions
import aetcd.rpc
import aetcd.utils


@pytest.mark.asyncio
async def test_watch_key(etcdctl, etcd):
    def update_etcd(v):
        etcdctl('put', '/key', v)
        result = etcdctl('get', '/key')
        assert base64.b64decode(result['kvs'][0]['value']) == aetcd.utils.to_bytes(v)

    def update_key():
        # Sleep to make watch can get the event
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
    events_iterator, cancel = await etcd.watch(b'/key')
    async for event in events_iterator:
        assert event.key == b'/key'
        assert event.value == aetcd.utils.to_bytes(str(change_count))

        # If cancel worked, we should not receive event 3
        assert event.value != b'3'

        change_count += 1
        if change_count > 2:
            # If cancel not work, we will block in this for-loop forever
            await cancel()

    t.join()


@pytest.mark.asyncio
async def test_watch_key_with_revision_compacted(etcdctl, etcd):
    etcdctl('put', '/key', '0')  # Some data to compact
    result = await etcd.get(b'/key')
    revision = result.mod_revision

    # Compact etcd and test watcher
    await etcd.compact(revision)

    def update_etcd(v):
        etcdctl('put', '/key', v)
        result = etcdctl('get', '/key')
        assert base64.b64decode(result['kvs'][0]['value']) == aetcd.utils.to_bytes(v)

    def update_key():
        update_etcd('1')
        update_etcd('2')
        update_etcd('3')

    t = threading.Thread(name='update_key', target=update_key)
    t.start()

    async def watch_compacted_revision_test():
        events_iterator, cancel = await etcd.watch(
            b'/key', start_revision=(revision - 1))

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
            b'/key', start_revision=compacted_revision)
        async for event in events_iterator:
            assert event.key == b'/key'
            assert event.value == aetcd.utils.to_bytes(str(change_count))

            # If cancel worked, we should not receive event 3
            assert event.value != aetcd.utils.to_bytes('3')

            change_count += 1
            if change_count > 2:
                await cancel()

    await watch_compacted_revision_test()

    t.join()


@pytest.mark.asyncio
async def test_watch_exception_during_watch(mocker, etcd, rpc_error):
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

    watcher_mock = mocker.AsyncMock()
    watcher_mock.add_callback = add_callback_mock
    etcd._watcher = watcher_mock

    events_iterator, cancel = await etcd.watch('foo')

    with pytest.raises(aetcd.exceptions.ConnectionFailedError):
        async for _ in events_iterator:
            pass

    await task


@pytest.mark.asyncio
async def test_watch_timeout_on_establishment(mocker, rpc_error):
    mocked_aiter = mocker.AsyncMock()
    mocked_aiter.side_effect = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)

    async with aetcd.Client(timeout=3) as etcd:
        etcd._watcher._watchstub.Watch.__aiter__ = mocked_aiter

        with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
            events_iterator, cancel = await etcd.watch(b'key')
            async for _ in events_iterator:
                pass


@pytest.mark.asyncio
async def test_watch_prefix(etcdctl, etcd):
    def update_etcd(v):
        etcdctl('put', '/key' + v, v)
        result = etcdctl('get', '/key' + v)
        assert base64.b64decode(result['kvs'][0]['value']) == aetcd.utils.to_bytes(v)

    def update_key():
        # Sleep to make watch can get the event
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
        '/key')
    async for event in events_iterator:
        assert event.key == aetcd.utils.to_bytes(f'/key{change_count}')
        assert event.value == aetcd.utils.to_bytes(str(change_count))

        # If cancel worked, we should not receive event 3
        assert event.value != b'3'

        change_count += 1
        if change_count > 2:
            # If cancel not work, we will block in this for-loop forever
            await cancel()

    t.join()


@pytest.mark.asyncio
async def test_watch_prefix_once_sequential(etcd):
    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once('/key', 1)

    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once('/key', 1)

    with pytest.raises(aetcd.exceptions.WatchTimeoutError):
        await etcd.watch_prefix_once('/key', 1)
