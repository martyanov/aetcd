class Lease(object):
    """A lease.

    :param id: ID of the lease
    :param ttl: time to live for this lease
    :param etcd_client: Instance of :class:`aetcd3.Etcd3Client`
    """

    def __init__(self, lease_id, ttl, etcd_client):
        self.id = lease_id
        self.ttl = ttl

        self._etcd_client = etcd_client

    async def _get_lease_info(self, *, keys=True):
        return await self._etcd_client.get_lease_info(self.id, keys=keys)

    async def revoke(self):
        """Revoke this lease."""
        await self._etcd_client.revoke_lease(self.id)

    async def refresh(self):
        """Refresh the time to live for this lease."""
        return await self._etcd_client.refresh_lease(self.id)

    async def remaining_ttl(self):
        """Return remaining time to live for this lease."""
        return (await self._get_lease_info(keys=False)).TTL

    async def granted_ttl(self):
        """Return granted time to live for this lease."""
        return (await self._get_lease_info(keys=False)).grantedTTL

    async def keys(self):
        """Return list of keys associated with this lease."""
        return (await self._get_lease_info()).keys
