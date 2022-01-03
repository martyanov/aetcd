import asyncio

import pytest


@pytest.mark.asyncio
async def test_lease_grant(etcd):
    lease = await etcd.lease(1)

    assert isinstance(lease.ttl, int)
    assert isinstance(lease.id, int)


@pytest.mark.asyncio
async def test_lease_revoke(etcd):
    lease = await etcd.lease(1)
    await lease.revoke()


@pytest.mark.asyncio
async def test_lease_keys_empty(etcd):
    lease = await etcd.lease(1)
    assert (await lease.keys()) == []


@pytest.mark.asyncio
async def test_lease_single_key(etcd):
    lease = await etcd.lease(1)
    await etcd.put(b'/doot/lease_test', b'this is a lease', lease=lease)
    assert (await lease.keys()) == [b'/doot/lease_test']


@pytest.mark.asyncio
async def test_lease_expire(etcd):
    key = b'/doot/lease_test_expire'
    lease = await etcd.lease(1)
    await etcd.put(key, b'this is a lease', lease=lease)
    assert (await lease.keys()) == [key]
    result = await etcd.get(key)
    assert result.value == b'this is a lease'
    assert (await lease.remaining_ttl()) <= (await lease.granted_ttl())

    # Wait for the lease to expire
    await asyncio.sleep((await lease.granted_ttl()) + 2)
    result = await etcd.get(key)
    assert result is None
