import tempfile

import pytest

import aetcd.exceptions
import aetcd.rpc


@pytest.fixture
async def etcd(etcd):
    yield etcd
    await etcd.disarm_alarm()
    async for m in etcd.members():
        if m.active_alarms:
            await etcd.disarm_alarm(m.id)


@pytest.mark.asyncio
async def test_create_alarm_all_members(etcd):
    alarms = await etcd.create_alarm()

    assert len(alarms) == 1
    assert alarms[0].member_id == 0
    assert alarms[0].alarm_type == aetcd.rpc.NOSPACE


@pytest.mark.asyncio
async def test_create_alarm_specific_member(etcd):
    members = [m async for m in etcd.members()]
    a_member = members[0]

    alarms = await etcd.create_alarm(member_id=a_member.id)

    assert len(alarms) == 1
    assert alarms[0].member_id == a_member.id
    assert alarms[0].alarm_type == aetcd.rpc.NOSPACE


@pytest.mark.asyncio
async def test_list_alarms(etcd):
    members = [m async for m in etcd.members()]
    a_member = members[0]
    await etcd.create_alarm()
    await etcd.create_alarm(member_id=a_member.id)
    possible_member_ids = [0, a_member.id]

    alarms = [a async for a in etcd.list_alarms()]

    assert len(alarms) == 2
    for alarm in alarms:
        possible_member_ids.remove(alarm.member_id)
        assert alarm.alarm_type == aetcd.rpc.NOSPACE

    assert possible_member_ids == []


@pytest.mark.asyncio
async def test_disarm_alarm(etcd):
    await etcd.create_alarm()
    assert len([a async for a in etcd.list_alarms()]) == 1

    await etcd.disarm_alarm()
    assert len([a async for a in etcd.list_alarms()]) == 0


@pytest.mark.asyncio
async def test_status_member(etcd):
    status = await etcd.status()

    assert isinstance(status.leader, aetcd.members.Member) is True
    assert status.leader.id in [m.id async for m in etcd.members()]


@pytest.mark.asyncio
async def test_hash(etcd):
    assert isinstance((await etcd.hash()), int)


@pytest.mark.asyncio
async def test_snapshot(etcdctl, etcd):
    with tempfile.NamedTemporaryFile() as f:
        await etcd.snapshot(f)
        f.flush()

        await etcdctl('snapshot', 'status', f.name)
