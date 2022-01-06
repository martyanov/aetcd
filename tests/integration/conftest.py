import json
import os
import subprocess
import urllib.parse

import pytest
import tenacity

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
async def etcd(etcdctl):
    endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
    host = 'localhost'
    port = 2379
    if endpoint:
        url = urllib.parse.urlparse(endpoint)
        host = url.hostname
        port = url.port

    async with aetcd.Client(
        host=host,
        port=port,
    ) as client:
        yield client

    @tenacity.retry(
        wait=tenacity.wait_fixed(2),
        stop=tenacity.stop_after_attempt(3),
    )
    def _delete_keys():
        etcdctl('del', '--prefix', '')
        result = etcdctl('get', '--prefix', '')
        assert 'kvs' not in result

    _delete_keys()
