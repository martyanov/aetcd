class ClientError(Exception):
    """The most generic client error."""


class ConnectionFailedError(ClientError):
    """Raises on etcd server connection errors."""

    def __str__(self):
        return 'etcd connection failed'


class ConnectionTimeoutError(ClientError):
    """Raises on etcd server connection timeout errors."""

    def __str__(self):
        return 'etcd connection timeout'


class InternalServerError(ClientError):
    """Raises on etcd internal server errors."""


class PreconditionFailedError(ClientError):
    """Raises on etcd server precondition errors."""


class RevisionCompactedError(ClientError):
    """Raises when requested and previous revisions were already compacted.

    :param compacted_revision: Revision bellow values were compacted
    :type compacted_revision: int
    """

    def __init__(self, compacted_revision):
        self.compacted_revision = compacted_revision
        super(RevisionCompactedError, self).__init__()


class WatchTimeoutError(ClientError):
    """Raises on operation timeouts."""
