import pytest

import aetcd


@pytest.mark.asyncio
@pytest.fixture
async def etcd_auth(etcdctl):
    await etcdctl('user', 'add', 'root:pwd')
    await etcdctl('auth', 'enable', ignore_result=True)

    yield

    await etcdctl('--user', 'root:pwd', 'auth', 'disable', ignore_result=True)
    await etcdctl('role', 'delete', 'root')
    await etcdctl('user', 'delete', 'root')


@pytest.mark.asyncio
async def test_auth(etcd_auth):
    client = aetcd.Client(
        username='root',
        password='pwd',
    )
    await client.get(b'key')
