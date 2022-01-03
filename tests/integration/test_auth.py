import pytest

import aetcd


@pytest.fixture
def etcd_auth(etcdctl):
    etcdctl('user', 'add', 'root:pwd')
    etcdctl('auth', 'enable', ignore_result=True)

    yield

    etcdctl('--user', 'root:pwd', 'auth', 'disable', ignore_result=True)
    etcdctl('role', 'delete', 'root')
    etcdctl('user', 'delete', 'root')


@pytest.mark.asyncio
async def test_auth(etcd_auth):
    client = aetcd.Client(
        username='root',
        password='pwd',
    )
    await client.get(b'key')
