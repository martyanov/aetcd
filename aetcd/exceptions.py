from . import rpc


class ClientError(Exception):
    """The most generic client error."""


class ConnectionFailedError(ClientError):
    """Raises on etcd server connection errors."""


class ConnectionTimeoutError(ClientError):
    """Raises on etcd server connection timeout errors."""


class InternalError(ClientError):
    """Raises on etcd internal errors."""


class InvalidArgumentError(ClientError):
    """Raises on errors associated with incorrect arguments being provided."""


class UnauthenticatedError(ClientError):
    """Raises on etcd unauthenticated errors."""


class PreconditionFailedError(ClientError):
    """Raises on etcd server precondition errors."""


class DuplicateLeaseError(ClientError):
    """Raised on attempt to create lease with already existing id."""


class RevisionCompactedError(ClientError):
    """Raises when requested and previous revisions were already compacted."""

    def __init__(self, compacted_revision):
        #: Revision bellow values were compacted.
        self.compacted_revision = compacted_revision

        super(RevisionCompactedError, self).__init__(
            f'revision was already compacted below {self.compacted_revision!r}',
        )


class WatchTimeoutError(ClientError):
    """Raises on watch operation timeouts.

    Please note, this error is different from ``ConnectionTimeoutError`` and
    may be raised only in two cases: when watch create operation was not completed
    in time and when watch event was not emitted within provided timeout.
    """


_EXCEPTIONS_BY_CODE = {
    rpc.StatusCode.DEADLINE_EXCEEDED: ConnectionTimeoutError,
    rpc.StatusCode.FAILED_PRECONDITION: PreconditionFailedError,
    rpc.StatusCode.INTERNAL: InternalError,
    rpc.StatusCode.INVALID_ARGUMENT: InvalidArgumentError,
    rpc.StatusCode.UNAVAILABLE: ConnectionFailedError,
    rpc.StatusCode.UNAUTHENTICATED: UnauthenticatedError,
}


def _handle_exception(error: Exception):
    # If the error is one of the client errors, raise as is
    if isinstance(error, ClientError):
        raise error

    # Query RPC error mapping and raise one of the matched client errors
    if isinstance(error, rpc.AioRpcError):
        e = _EXCEPTIONS_BY_CODE.get(error.code())
        error_details = error.details()

        if e is not None:
            if e is PreconditionFailedError and 'lease already exists' in error_details:
                raise DuplicateLeaseError
            raise e(error_details) from error
        raise ClientError(error_details) from error

    # Fallback to wrap original error with the client error
    raise ClientError(error)
