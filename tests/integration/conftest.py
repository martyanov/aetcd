import asyncio
import asyncio.subprocess
import contextlib
import json
import os
import urllib.parse

import pytest

import aetcd


@pytest.fixture(scope='session', autouse=True)
def setup():
    os.environ['ETCDCTL_API'] = '3'


@pytest.fixture(scope='session')
@pytest.mark.asyncio
def etcdctl():
    async def _etcdctl(*args, ignore_result=False):
        endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
        if endpoint:
            args = ['--endpoints', endpoint] + list(args)
        args = ['etcdctl', '-w', 'json'] + list(args)

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise Exception(f'Error during awaiting process with args {args!r}: {stderr}')

        if ignore_result:
            return None

        return json.loads(stdout.decode('utf-8'))
    return _etcdctl


@pytest.fixture
async def client(etcdctl):
    host = 'localhost'
    port = 2379

    endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
    if endpoint:
        url = urllib.parse.urlparse(endpoint)
        host = url.hostname
        port = url.port

    @contextlib.asynccontextmanager
    async def _client(
        host=host,
        port=port,
        username=None,
        password=None,
        timeout=None,
        options=None,
    ):
        async with aetcd.Client(
            host=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            options={
                'keepalive_time_ms': 6000,
                'keepalive_permit_without_calls': True,
                'http2_max_pings_without_data': 0,
            },
        ) as client:
            yield client

        await etcdctl('del', '--prefix', '')
        result = await etcdctl('get', '--prefix', '')
        assert 'kvs' not in result

    return _client


@pytest.fixture
async def etcd(client):
    async with client() as etcd:
        yield etcd
