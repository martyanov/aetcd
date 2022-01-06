import asyncio

import pytest

import aetcd
import aetcd.exceptions


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
    mocked_aiter = mocker.AsyncMock()
    mocked_aiter.side_effect = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)

    async with aetcd.Client(timeout=3) as etcd:
        etcd._watcher._watchstub.Watch.__aiter__ = mocked_aiter

        with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
            async for _ in await etcd.watch(b'key'):
                pass
