import pytest


@pytest.fixture
def response_header(mocker):
    rh = mocker.Mock()
    rh.cluster_id = 1
    rh.member_id = 2
    rh.revision = 3
    rh.raft_term = 4
    return rh


@pytest.fixture
def keyvalue(mocker):
    kv = mocker.Mock()
    kv.key = b'k'
    kv.value = b'v'
    kv.create_revision = 11
    kv.mod_revision = 12
    kv.version = 13
    kv.lease = 14
    return kv
