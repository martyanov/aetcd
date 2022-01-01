import aetcd.rtypes


def test__slotted_type():
    class Slotted(aetcd.rtypes._Slotted):
        __slots__ = ['a', 'b']

        def __init__(self, a, b):
            self.a = a
            self.b = b

    _slotted = aetcd.rtypes._Slotted()

    assert str(_slotted) == repr(_slotted) == '_Slotted[]'
    assert _slotted.__slots__ == []

    slotted = Slotted(1, 2)

    assert getattr(slotted, '__dict__', None) is None
    assert slotted.__slots__ == [
        'a',
        'b',
    ]
    assert slotted.a == 1
    assert slotted.b == 2
    assert str(slotted) == repr(slotted) == 'Slotted[a=1, b=2]'


def test_response_header_type(response_header):
    rh = aetcd.rtypes.ResponseHeader(response_header)

    assert getattr(rh, '__dict__', None) is None
    assert rh.__slots__ == [
        'cluster_id',
        'member_id',
        'revision',
        'raft_term',
    ]
    assert rh.cluster_id == response_header.cluster_id
    assert rh.member_id == response_header.member_id
    assert rh.revision == response_header.revision
    assert rh.raft_term == response_header.raft_term


def test_key_value_type(keyvalue):
    kv = aetcd.rtypes.KeyValue(keyvalue)

    assert getattr(kv, '__dict__', None) is None
    assert kv.__slots__ == [
        'key',
        'value',
        'create_revision',
        'mod_revision',
        'version',
        'lease',
    ]
    assert kv.key == keyvalue.key
    assert kv.value == keyvalue.value
    assert kv.create_revision == keyvalue.create_revision
    assert kv.mod_revision == keyvalue.mod_revision
    assert kv.version == keyvalue.version
    assert kv.lease == keyvalue.lease


def test_get_type(response_header, keyvalue):
    g = aetcd.rtypes.Get(response_header, keyvalue)

    assert getattr(g, '__dict__', None) is None
    assert g.__slots__ == [
        'header',
        'key',
        'value',
        'create_revision',
        'mod_revision',
        'version',
        'lease',
    ]
    assert g.header.cluster_id == response_header.cluster_id
    assert g.header.member_id == response_header.member_id
    assert g.header.revision == response_header.revision
    assert g.header.raft_term == response_header.raft_term
    assert g.key == keyvalue.key
    assert g.value == keyvalue.value
    assert g.create_revision == keyvalue.create_revision
    assert g.mod_revision == keyvalue.mod_revision
    assert g.version == keyvalue.version
    assert g.lease == keyvalue.lease


def test_get_range_type(response_header, keyvalues):
    gr = aetcd.rtypes.GetRange(response_header, keyvalues, False, 3)

    assert gr.header.cluster_id == response_header.cluster_id
    assert gr.header.member_id == response_header.member_id
    assert gr.header.revision == response_header.revision
    assert gr.header.raft_term == response_header.raft_term
    assert gr
    assert bool(gr) is True
    assert gr.more is False
    assert len(gr) == gr.count == 3
    for i, g in enumerate(gr):
        assert type(g) is aetcd.rtypes.KeyValue
        assert type(gr[i]) is aetcd.rtypes.KeyValue
        assert g.key == gr[i].key == keyvalues[i].key
        assert g.value == gr[i].value == keyvalues[i].value
        assert g.create_revision == gr[i].create_revision == keyvalues[i].create_revision
        assert g.mod_revision == gr[i].mod_revision == keyvalues[i].mod_revision
        assert g.version == gr[i].version == keyvalues[i].version
        assert g.lease == gr[i].lease == keyvalues[i].lease
    assert gr.kvs == keyvalues
    assert str(gr) == repr(gr) == (
        f'GetRange[header={gr.header!r}, more={gr.more!r}, count={gr.count!r}]'
    )

    gr = aetcd.rtypes.GetRange(response_header, [], False, 0)

    assert not gr
    assert bool(gr) is False
    assert len(gr) == gr.count == 0
