import typing


class _Slotted:

    __slots__ = []

    def __repr__(self):
        return f'{self.__class__.__name__}[' + ', '.join(
            f'{attr}={getattr(self, attr)}'
            for attr in self.__slots__
        ) + ']'


class ResponseHeader(_Slotted):
    """Represents the metadata for the response."""

    __slots__ = [
        'cluster_id',
        'member_id',
        'revision',
        'raft_term',
    ]

    def __init__(self, header):
        #: The ID of the cluster which sent the response.
        self.cluster_id: int = header.cluster_id

        #: The ID of the member which sent the response.
        self.member_id: int = header.member_id

        #: The key-value store revision when the request was applied.
        #: For watch progress responses, the revision indicates progress.
        #: All future events recieved in this stream are guaranteed to have a higher
        #: revision number than the revision number.
        self.revision: int = header.revision

        #: The raft term when the request was applied.
        self.raft_term: int = header.raft_term


class KeyValue(_Slotted):
    """Represents the requested key-value."""

    __slots__ = [
        'key',
        'value',
        'create_revision',
        'mod_revision',
        'version',
        'lease',
    ]

    def __init__(self, keyvalue):
        #: Key in bytes, empty key is not allowed.
        self.key: bytes = keyvalue.key

        #: Value held by the key, in bytes.
        self.value: bytes = keyvalue.value

        #: Revision of last creation on this key.
        self.create_revision: int = keyvalue.create_revision

        #: Revision of last modificatioin on this key.
        self.mod_revision: int = keyvalue.mod_revision

        #: Version of the key, a deletion resets the version to zero and any
        #: modification of the key increases its version.
        self.version: int = keyvalue.version

        #: ID of the lease that attached to the key, when the attached
        #: lease expires, the key will be deleted, if the lease is zero,
        #: then no lease is attached to the key.
        self.lease: int = keyvalue.lease


class Get(KeyValue):
    """Represents the result of get operations."""

    __slots__ = [
        'header',
    ] + KeyValue.__slots__

    def __init__(self, header, keyvalue):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        super().__init__(keyvalue)


class Put(_Slotted):
    """Represents the result of put operations."""

    __slots__ = [
        'header',
        'prev_kv',
    ]

    def __init__(self, header, prev_kv=None):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        #: If ``prev_kv`` flag was set in the request,
        #: the previous key-value pair will be stored in this attribute.
        self.prev_kv: typing.Optional[KeyValue] = KeyValue(prev_kv) if prev_kv else None


class Delete(_Slotted):
    """Represents the result of delete operations.

    If a number of deleted keys is above zero, iterpret the result as truthy,
    otherwise as falsy.
    """

    __slots__ = [
        'header',
        'deleted',
        'prev_kv',
    ]

    def __init__(self, header, deleted, prev_kv=None):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        #: The number of keys deleted by the delete request.
        self.deleted = deleted

        #: If ``prev_kv`` flag was set in the request,
        #: the previous key-value pair will be stored in this attribute.
        self.prev_kv: typing.Optional[KeyValue] = KeyValue(prev_kv) if prev_kv else None

    def __bool__(self):
        return self.deleted > 0
