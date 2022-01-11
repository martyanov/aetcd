import asyncio

import pytest


@pytest.mark.asyncio
async def test_lock_acquire(etcd):
    lock = etcd.lock(b'key', ttl=10)
    assert (await lock.acquire()) is True
    assert (await etcd.get(lock.key)).value is not None
    assert (await lock.acquire(timeout=0)) is False
    assert (await lock.acquire(timeout=1)) is False


@pytest.mark.asyncio
async def test_lock_release(etcd):
    lock = etcd.lock(b'key', ttl=10)
    assert (await lock.acquire()) is True
    assert (await etcd.get(lock.key)).value is not None
    assert (await lock.release()) is True

    result = await etcd.get(lock.key)
    assert result is None
    assert (await lock.acquire()) is True
    assert (await lock.release()) is True
    assert (await lock.acquire(timeout=None)) is True


@pytest.mark.asyncio
async def test_lock_expire(etcd):
    lock = etcd.lock(b'key', ttl=2)
    assert (await lock.acquire()) is True
    assert (await etcd.get(lock.key)).value is not None
    # Wait for the lease to expire
    await asyncio.sleep(3)
    result = await etcd.get(lock.key)
    assert result is None


@pytest.mark.asyncio
async def test_lock_refresh(etcd):
    lock = etcd.lock(b'key', ttl=3)
    assert (await lock.acquire()) is True
    assert (await etcd.get(lock.key)).value is not None

    # Sleep for the same total time as test_lock_expire, but refresh each
    # second
    for _ in range(4):
        await asyncio.sleep(1)
        await lock.refresh()

    assert (await etcd.get(lock.key)).value is not None


@pytest.mark.asyncio
async def test_lock_is_acquired(etcd):
    lock1 = etcd.lock(b'key', ttl=2)
    assert (await lock1.is_acquired()) is False

    lock2 = etcd.lock(b'key', ttl=2)
    await lock2.acquire()
    assert (await lock2.is_acquired()) is True
    await lock2.release()

    lock3 = etcd.lock(b'key', ttl=2)
    await lock3.acquire()
    assert (await lock3.is_acquired()) is True
    assert (await lock2.is_acquired()) is False


@pytest.mark.asyncio
async def test_lock_context_manager(etcd):
    async with etcd.lock(b'key', ttl=2) as lock:
        assert (await lock.is_acquired()) is True
    assert (await lock.is_acquired()) is False


@pytest.mark.asyncio
async def test_lock_contended(etcd):
    lock1 = etcd.lock(b'key', ttl=2)
    await lock1.acquire()

    lock2 = etcd.lock(b'key', ttl=2)
    await lock2.acquire()

    assert (await lock1.is_acquired()) is False
    assert (await lock2.is_acquired()) is True


@pytest.mark.asyncio
async def test_lock_double_acquire_release(etcd):
    lock = etcd.lock(b'key', ttl=5)

    assert (await lock.acquire(0)) is True
    assert (await lock.acquire(0)) is False
    assert (await lock.release()) is True


@pytest.mark.asyncio
async def test_lock_acquire_none(etcd):
    lock = etcd.lock(b'key', ttl=5)

    assert (await lock.acquire(None)) is True

    # This will succeed after 5 seconds since the TTL will expire and the
    # lock is not refreshed
    assert (await lock.acquire(None)) is True
