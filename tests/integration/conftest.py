import json
import os
import subprocess

import pytest


@pytest.fixture(scope='session', autouse=True)
def setup():
    os.environ['ETCDCTL_API'] = '3'


@pytest.fixture(scope='session')
def etcdctl():
    def _etcdctl(*args):
        endpoint = os.environ.get('TEST_ETCD_HTTP_URL')
        if endpoint:
            args = ['--endpoints', endpoint] + list(args)
        args = ['etcdctl', '-w', 'json'] + list(args)
        output = subprocess.check_output(args)
        return json.loads(output.decode('utf-8'))
    return _etcdctl
