import asyncio

import pytest

import aetcd.exceptions


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
    await etcd.put(b'/key', b'value', lease=lease)
    assert (await lease.keys()) == [b'/key']


@pytest.mark.asyncio
async def test_lease_expire(etcd):
    key = b'/key'
    lease = await etcd.lease(1)
    await etcd.put(key, b'value', lease=lease)
    assert (await lease.keys()) == [key]
    result = await etcd.get(key)
    assert result.value == b'value'
    assert (await lease.remaining_ttl()) <= (await lease.granted_ttl())

    # Wait for the lease to expire
    await asyncio.sleep((await lease.granted_ttl()) + 1)
    result = await etcd.get(key)
    assert result is None


@pytest.mark.asyncio
async def test_lease_create_with_already_existing_id(etcd):
    await etcd.lease(10, lease_id=123)

    with pytest.raises(aetcd.exceptions.DuplicateLeaseError):
        await etcd.lease(15, lease_id=123)
