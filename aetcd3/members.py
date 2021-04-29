class Member:
    """A member of the etcd cluster.

    :param id: ID of the cluster member
    :param name: Human-readable name of the cluster member
    :param peer_urls: List of URLs the cluster member exposes to the cluster for
                     communication
    :param client_urls: List of URLs the cluster member exposes to clients for
                       communication
    :param etcd_client: Instance of :class:`aetcd3.client.Etcd3Client`
    """

    def __init__(self, id, name, peer_urls, client_urls, etcd_client):
        self.id = id
        self.name = name
        self.peer_urls = peer_urls
        self.client_urls = client_urls

        self._etcd_client = etcd_client

    def __str__(self):
        return (
            f'Cluster member with ID: {self.id}, peer URLs: {self.peer_urls}, client '
            f'URLs: {self.client_urls}'
        )

    async def remove(self):
        """Remove this cluster member from the cluster."""
        await self._etcd_client.remove_member(self.id)

    async def update(self, peer_urls):
        """Update the configuration of this cluster member.

        :param peer_urls: New list of peer URLs the cluster member will use to
                          communicate with the cluster
        """
        await self._etcd_client.update_member(self.id, peer_urls)

    async def active_alarms(self):
        """Get active alarms of the cluster member.

        :returns: List of :class:`aetcd3.client.Alarm`
        """
        return await self._etcd_client.list_alarms(member_id=self.id)
