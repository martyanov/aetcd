import pytest


@pytest.mark.skipif(
    "config.getoption('--with-cluster') is False",
    reason='ETCD cluster was not run',
)
@pytest.mark.asyncio
async def test_member_list(etcd):
    assert len([m async for m in etcd.members()]) == 3
    async for member in etcd.members():
        assert member.name.startswith('pifpaf')
        for peer_url in member.peer_urls:
            assert peer_url.startswith('http://')
        for client_url in member.client_urls:
            assert client_url.startswith('http://')
        assert isinstance(member.id, int) is True
