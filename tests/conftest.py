import pytest

import aetcd
import aetcd.rpc


def pytest_addoption(parser):
    parser.addoption(
        '--with-cluster',
        action='store_true',
        default=False,
        help='Run tests with ETCD cluster',
    )


@pytest.fixture
async def etcd():
    # TODO: Rewrite the mock and related tests without side-effects
    async with aetcd.Client() as client:
        yield client


@pytest.fixture
def rpc_error(mocker):
    def _rpc_error(code, details=''):
        return aetcd.rpc.AioRpcError(
            code=code,
            initial_metadata=mocker.Mock(),
            trailing_metadata=mocker.Mock(),
            details=details,
        )
    return _rpc_error


@pytest.fixture
def response_header(mocker):
    rh = mocker.Mock()
    rh.cluster_id = 1
    rh.member_id = 2
    rh.revision = 3
    rh.raft_term = 4
    return rh


@pytest.fixture
def key_value_maker(mocker):
    def _key_value_maker(key, value, create_revision, mod_revision, version, lease):
        kv = mocker.Mock()
        kv.key = key
        kv.value = value
        kv.create_revision = create_revision
        kv.mod_revision = mod_revision
        kv.version = version
        kv.lease = lease
        return kv
    return _key_value_maker


@pytest.fixture
def key_value(key_value_maker):
    return key_value_maker(b'k', b'v', 11, 12, 13, 14)


@pytest.fixture
def key_values(key_value_maker):
    return [
        key_value_maker(*(b'k1', b'v1', 11, 12, 13, 14)),
        key_value_maker(*(b'k2', b'v2', 11, 12, 13, 14)),
        key_value_maker(*(b'k3', b'v3', 11, 12, 13, 14)),
    ]
