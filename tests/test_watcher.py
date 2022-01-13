import asyncio

import pytest

import aetcd
import aetcd.exceptions
import aetcd.watcher


@pytest.mark.asyncio
async def test_watch_with_exception_during_watch(mocker, etcd, rpc_error):
    async def pass_exception_to_callback(callback):
        await asyncio.sleep(1)
        e = rpc_error(aetcd.rpc.StatusCode.UNAVAILABLE)
        await callback(e)

    task = None

    async def add_callback_mock(*args, **kwargs):
        nonlocal task
        callback = args[1]
        task = asyncio.get_event_loop().create_task(
            pass_exception_to_callback(callback))
        watcher_callback = aetcd.watcher.WatcherCallback(callback)
        watcher_callback.watch_id = 1
        return watcher_callback

    watcher_mock = mocker.AsyncMock()
    watcher_mock.add_callback = add_callback_mock
    etcd._watcher = watcher_mock

    with pytest.raises(aetcd.exceptions.ConnectionFailedError):
        async for _ in await etcd.watch(b'key'):
            pass

    await task


@pytest.mark.asyncio
async def test_watch_with_timeout_on_connect(mocker, rpc_error):
    mocked_iter = mocker.AsyncMock()
    mocked_iter.__aiter__.side_effect = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)
    mocked_watch = mocker.Mock(return_value=mocked_iter)

    async with aetcd.Client(timeout=3) as etcd:
        etcd._watcher._watchstub.Watch = mocked_watch

        with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
            async for _ in await etcd.watch(b'key'):
                pass


@pytest.mark.asyncio
async def test_watcher_with_wrong_kind(mocker):
    watcher = aetcd.watcher.Watcher(mocker.Mock())

    with pytest.raises(
        TypeError,
        match='an instance of EventKind should be provided',
    ):
        await watcher.add_callback(b'key', None, kind='put')
