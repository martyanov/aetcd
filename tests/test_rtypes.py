import pytest

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


def test_key_value_type(key_value):
    kv = aetcd.rtypes.KeyValue(key_value)

    assert getattr(kv, '__dict__', None) is None
    assert kv.__slots__ == [
        'key',
        'value',
        'create_revision',
        'mod_revision',
        'version',
        'lease',
    ]
    assert kv.key == key_value.key
    assert kv.value == key_value.value
    assert kv.create_revision == key_value.create_revision
    assert kv.mod_revision == key_value.mod_revision
    assert kv.version == key_value.version
    assert kv.lease == key_value.lease


def test_get_type(response_header, key_value):
    g = aetcd.rtypes.Get(response_header, key_value)

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
    assert g.key == key_value.key
    assert g.value == key_value.value
    assert g.create_revision == key_value.create_revision
    assert g.mod_revision == key_value.mod_revision
    assert g.version == key_value.version
    assert g.lease == key_value.lease


def test_get_range_type(response_header, key_values):
    gr = aetcd.rtypes.GetRange(response_header, key_values, False, 3)

    assert gr
    assert bool(gr) is True
    assert gr.more is False
    assert len(gr) == gr.count == 3
    assert gr.header.cluster_id == response_header.cluster_id
    assert gr.header.member_id == response_header.member_id
    assert gr.header.revision == response_header.revision
    assert gr.header.raft_term == response_header.raft_term
    for i, g in enumerate(gr):
        assert type(g) is aetcd.rtypes.KeyValue
        assert type(gr[i]) is aetcd.rtypes.KeyValue
        assert g.key == gr[i].key == key_values[i].key
        assert g.value == gr[i].value == key_values[i].value
        assert g.create_revision == gr[i].create_revision == key_values[i].create_revision
        assert g.mod_revision == gr[i].mod_revision == key_values[i].mod_revision
        assert g.version == gr[i].version == key_values[i].version
        assert g.lease == gr[i].lease == key_values[i].lease
    assert gr.kvs == key_values
    assert str(gr) == repr(gr) == (
        f'GetRange[header={gr.header!r}, more={gr.more!r}, count={gr.count!r}]'
    )

    gr = aetcd.rtypes.GetRange(response_header, [], False, 0)

    assert not gr
    assert bool(gr) is False
    assert len(gr) == gr.count == 0
    assert gr.kvs == []


def test_put_type(response_header, key_value):
    p = aetcd.rtypes.Put(response_header, key_value)

    assert getattr(p, '__dict__', None) is None
    assert p.__slots__ == [
        'header',
        'prev_kv',
    ]
    assert p.header.cluster_id == response_header.cluster_id
    assert p.header.member_id == response_header.member_id
    assert p.header.revision == response_header.revision
    assert p.header.raft_term == response_header.raft_term
    assert type(p.prev_kv) is aetcd.rtypes.KeyValue
    assert p.prev_kv.key == key_value.key
    assert p.prev_kv.value == key_value.value
    assert p.prev_kv.create_revision == key_value.create_revision
    assert p.prev_kv.mod_revision == key_value.mod_revision
    assert p.prev_kv.version == key_value.version
    assert p.prev_kv.lease == key_value.lease

    p = aetcd.rtypes.Put(response_header)

    assert p.prev_kv is None


def test_delete_type(response_header, key_value):
    d = aetcd.rtypes.Delete(response_header, 1, key_value)

    assert getattr(d, '__dict__', None) is None
    assert d.__slots__ == [
        'header',
        'deleted',
        'prev_kv',
    ]
    assert d.header.cluster_id == response_header.cluster_id
    assert d.header.member_id == response_header.member_id
    assert d.header.revision == response_header.revision
    assert d.header.raft_term == response_header.raft_term
    assert d.deleted == 1
    assert type(d.prev_kv) is aetcd.rtypes.KeyValue
    assert d.prev_kv.key == key_value.key
    assert d.prev_kv.value == key_value.value
    assert d.prev_kv.create_revision == key_value.create_revision
    assert d.prev_kv.mod_revision == key_value.mod_revision
    assert d.prev_kv.version == key_value.version
    assert d.prev_kv.lease == key_value.lease

    d = aetcd.rtypes.Delete(response_header, 1)

    assert d.deleted == 1
    assert d.prev_kv is None


def test_delete_range_type(response_header, key_values):
    dr = aetcd.rtypes.DeleteRange(response_header, 3, key_values)

    assert dr
    assert bool(dr) is True
    assert len(dr) == dr.deleted == 3
    assert dr.header.cluster_id == response_header.cluster_id
    assert dr.header.member_id == response_header.member_id
    assert dr.header.revision == response_header.revision
    assert dr.header.raft_term == response_header.raft_term
    for i, d in enumerate(dr):
        assert type(d) is aetcd.rtypes.KeyValue
        assert type(dr[i]) is aetcd.rtypes.KeyValue
        assert d.key == dr[i].key == key_values[i].key
        assert d.value == dr[i].value == key_values[i].value
        assert d.create_revision == dr[i].create_revision == key_values[i].create_revision
        assert d.mod_revision == dr[i].mod_revision == key_values[i].mod_revision
        assert d.version == dr[i].version == key_values[i].version
        assert d.lease == dr[i].lease == key_values[i].lease
    assert dr.prev_kvs == key_values
    assert str(dr) == repr(dr) == f'DeleteRange[header={dr.header!r}, deleted={dr.deleted!r}]'

    dr = aetcd.rtypes.DeleteRange(response_header, 0, [])

    assert not dr
    assert bool(dr) is False
    assert len(dr) == dr.deleted == 0
    assert dr.prev_kvs == []


def test_event_type(key_values):
    e = aetcd.rtypes.Event(aetcd.rpc.Event.EventType.PUT, key_values[1], key_values[0])

    assert getattr(e, '__dict__', None) is None
    assert e.__slots__ == [
        'kind',
        'kv',
        'prev_kv',
    ]
    assert e.kind == aetcd.rtypes.EventKind.PUT
    assert type(e.kv) is aetcd.rtypes.KeyValue
    assert e.kv.key == key_values[1].key
    assert e.kv.value == key_values[1].value
    assert e.kv.create_revision == key_values[1].create_revision
    assert e.kv.mod_revision == key_values[1].mod_revision
    assert e.kv.version == key_values[1].version
    assert e.kv.lease == key_values[1].lease
    assert type(e.prev_kv) is aetcd.rtypes.KeyValue
    assert e.prev_kv.key == key_values[0].key
    assert e.prev_kv.value == key_values[0].value
    assert e.prev_kv.create_revision == key_values[0].create_revision
    assert e.prev_kv.mod_revision == key_values[0].mod_revision
    assert e.prev_kv.version == key_values[0].version
    assert e.prev_kv.lease == key_values[0].lease

    e = aetcd.rtypes.Event(aetcd.rpc.Event.EventType.DELETE, key_values[0])

    assert e.kind == aetcd.rtypes.EventKind.DELETE
    assert e.prev_kv is None


@pytest.mark.asyncio
async def test_watch_type(mocker):
    async def iterator():
        yield 1
        yield 2
        yield 3

    cancel_func = mocker.AsyncMock()

    w = aetcd.rtypes.Watch(iterator, cancel_func, 1)

    evs = []
    async for e in w:
        evs.append(e)

    assert evs == [1, 2, 3]

    await w.cancel()

    cancel_func.assert_called_once()

    assert w.watch_id == 1
    assert str(w) == repr(w) == 'Watch[watch_id=1]'
