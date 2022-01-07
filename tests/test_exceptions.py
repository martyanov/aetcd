import pytest

import aetcd.exceptions
import aetcd.rpc


def test_revision_compacted_error_type():
    error = aetcd.exceptions.RevisionCompactedError(5)

    with pytest.raises(
        aetcd.exceptions.RevisionCompactedError,
            match='revision was already compacted below 5',
    ):
        raise error

    assert error.compacted_revision == 5


def test__handle_exception_with_client_errors():
    error = aetcd.exceptions.ClientError('client error')

    with pytest.raises(aetcd.exceptions.ClientError, match='client error'):
        aetcd.exceptions._handle_exception(error)


def test__handle_exception_with_known_rpc_errors(rpc_error):
    error = rpc_error(aetcd.rpc.StatusCode.DEADLINE_EXCEEDED)

    with pytest.raises(aetcd.exceptions.ConnectionTimeoutError):
        aetcd.exceptions._handle_exception(error)

    error = rpc_error(aetcd.rpc.StatusCode.FAILED_PRECONDITION)

    with pytest.raises(aetcd.exceptions.PreconditionFailedError):
        aetcd.exceptions._handle_exception(error)

    error = rpc_error(aetcd.rpc.StatusCode.INTERNAL)

    with pytest.raises(aetcd.exceptions.InternalError):
        aetcd.exceptions._handle_exception(error)

    error = rpc_error(aetcd.rpc.StatusCode.INVALID_ARGUMENT)

    with pytest.raises(aetcd.exceptions.InvalidArgumentError):
        aetcd.exceptions._handle_exception(error)

    error = rpc_error(aetcd.rpc.StatusCode.UNAVAILABLE)

    with pytest.raises(aetcd.exceptions.ConnectionFailedError):
        aetcd.exceptions._handle_exception(error)


def test__handle_exception_with_unknown_rpc_errors(rpc_error):
    error = rpc_error(aetcd.rpc.StatusCode.DATA_LOSS, 'disk failure')

    with pytest.raises(aetcd.exceptions.ClientError, match='disk failure'):
        aetcd.exceptions._handle_exception(error)


def test__handle_exception_with_unknown_errors(rpc_error):
    error = Exception('unknown error')

    with pytest.raises(aetcd.exceptions.ClientError, match='unknown error'):
        aetcd.exceptions._handle_exception(error)
