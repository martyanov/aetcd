class Etcd3Exception(Exception):
    """Raises on generic client errors."""


class WatchTimedOut(Etcd3Exception):
    """Raised on operation timeouts."""


class InternalServerError(Etcd3Exception):
    """Raises on etcd internal server errors."""


class ConnectionFailedError(Etcd3Exception):
    """Raises on etcd server connection errors."""

    def __str__(self):
        return 'etcd connection failed'


class ConnectionTimeoutError(Etcd3Exception):
    """Raises on etcd server connection timeout errors."""

    def __str__(self):
        return 'etcd connection timeout'


class PreconditionFailedError(Etcd3Exception):
    """Raises on etcd server precondition errors."""


class RevisionCompactedError(Etcd3Exception):
    """Raises when requested and previous revisions were already compacted.

    :param compacted_revision: Revision bellow values were compacted
    :type compacted_revision: int
    """

    def __init__(self, compacted_revision):
        self.compacted_revision = compacted_revision
        super(RevisionCompactedError, self).__init__()
