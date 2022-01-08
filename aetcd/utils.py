import typing

import aetcd.leases


def prefix_range_end(prefix: bytes) -> bytes:
    """Create a bytestring that can be used as a ``range_end`` for a prefix."""
    s = bytearray(prefix)
    for i in reversed(range(len(s))):
        if s[i] < 0xff:
            s[i] = s[i] + 1
            break
    return bytes(s)


def to_bytes(maybe_bytes: typing.Union[bytes, str]) -> bytes:
    """Encode string to bytes.

    Convenience function to do a simple ``encode('utf-8')`` if the input is not
    already bytes, return the data unmodified if the input is bytes.
    """
    if isinstance(maybe_bytes, bytes):
        return maybe_bytes
    else:
        return maybe_bytes.encode('utf-8')


def lease_to_id(lease: typing.Union[aetcd.leases.Lease, int]) -> int:
    """Resolve lease ID based on the provided argument.

    If provided argument is a :class:`~aetcd.leases.Lease` object, just return its
    ID,  otherwise cast provided argument to ``int`` and return the result
    or ``0`` if the cast failed.
    """
    if hasattr(lease, 'id'):
        return lease.id

    try:
        return int(lease)
    except TypeError:
        return 0
