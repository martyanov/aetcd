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
def keyvalue_maker(mocker):
    def _keyvalue_maker(key, value, create_revision, mod_revision, version, lease):
        kv = mocker.Mock()
        kv.key = key
        kv.value = value
        kv.create_revision = create_revision
        kv.mod_revision = mod_revision
        kv.version = version
        kv.lease = lease
        return kv
    return _keyvalue_maker


@pytest.fixture
def keyvalue(keyvalue_maker):
    return keyvalue_maker(b'k', b'v', 11, 12, 13, 14)


@pytest.fixture
def keyvalues(keyvalue_maker):
    return [
        keyvalue_maker(*(b'k1', b'v1', 11, 12, 13, 14)),
        keyvalue_maker(*(b'k2', b'v2', 11, 12, 13, 14)),
        keyvalue_maker(*(b'k3', b'v3', 11, 12, 13, 14)),
    ]
