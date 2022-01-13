import contextlib
import json
import os
import subprocess
import urllib.parse

import pytest

import aetcd


@pytest.fixture(scope='session', autouse=True)
def setup():
    os.environ['ETCDCTL_API'] = '3'


@pytest.fixture(scope='session')
def etcdctl():
    def _etcdctl(*args, ignore_result=False):
        endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
        if endpoint:
            args = ['--endpoints', endpoint] + list(args)
        args = ['etcdctl', '-w', 'json'] + list(args)
        output = subprocess.check_output(args)
        if ignore_result:
            return None
        return json.loads(output.decode('utf-8'))
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
            options=options,
        ) as client:
            yield client

        etcdctl('del', '--prefix', '')
        result = etcdctl('get', '--prefix', '')
        assert 'kvs' not in result

    return _client


@pytest.fixture
async def etcd(client):
    async with client() as etcd:
        yield etcd
