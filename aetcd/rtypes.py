import enum
import typing

from . import rpc


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
    """Represents the result of get operation."""

    __slots__ = [
        'header',
    ] + KeyValue.__slots__

    def __init__(self, header, keyvalue):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        super().__init__(keyvalue)


class GetRange:
    """Represents the result of get range operation.

    Implements ``__bool__``, ``__len__``, ``__iter__`` and ``__getitem__``.

    If a number of ``count`` keys is above zero iterpret the result as truthy,
    otherwise as falsy.

    It is possible to iterate over the collection or use indexing, as a result
    :class:`~aetcd.rtypes.KeyValue` will be returned.

    .. note::
        Also, it is possible to access raw ``kvs`` provided by the underlying
        ``RPC`` call, that is the most effective way to access the keys from performance
        and memory perspective, but keep in mind that the overall performance highly
        depends on usage pattern and the size of dataset, use wisely. Generally,
        it is recommended to use :class:`~aetcd.rtypes.KeyValue` wrapped results.
    """

    def __init__(self, header, kvs, more, count):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        #: The list of key-value pairs matched by the range request,
        #: empty when ``count_only`` flag was set in the request.
        self.kvs = kvs

        #: Indicates if there are more keys to return in the requested range.
        self.more: bool = more

        #: The number of keys within the requested range.
        self.count: int = count

    def __bool__(self):
        return self.count > 0

    def __len__(self):
        return len(self.kvs)

    def __iter__(self):
        for kv in self.kvs:
            yield KeyValue(kv)

    def __getitem__(self, index):
        return KeyValue(self.kvs[index])

    def __repr__(self):
        return (
            f'{self.__class__.__name__}'
            f'[header={self.header!r}, more={self.more!r}, count={self.count!r}]'
        )


class Put(_Slotted):
    """Represents the result of put operation."""

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
    """Represents the result of delete operation."""

    __slots__ = [
        'header',
        'deleted',
        'prev_kv',
    ]

    def __init__(self, header, deleted, prev_kv=None):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        #: The number of keys deleted by the delete request.
        self.deleted: int = deleted

        #: If ``prev_kv`` flag was set in the request,
        #: the previous key-value pair will be stored in this attribute.
        self.prev_kv: typing.Optional[KeyValue] = KeyValue(prev_kv) if prev_kv else None


class DeleteRange:
    """Represents the result of delete range operation.

    Implements ``__bool__``, ``__len__``, ``__iter__`` and ``__getitem__``.

    If a number of ``deleted`` keys is above zero iterpret the result as truthy,
    otherwise as falsy.

    It is possible to iterate over the collection or use indexing, as a result
    :class:`~aetcd.rtypes.KeyValue` will be returned.

    .. note::
        Also, it is possible to access raw ``prev_kvs`` provided by the underlying
        ``RPC`` call, that is the most effective way to access the keys from performance
        and memory perspective, but keep in mind that the overall performance highly
        depends on usage pattern and the size of dataset, use wisely. Generally,
        it is recommended to use :class:`~aetcd.rtypes.KeyValue` wrapped results.
    """

    def __init__(self, header, deleted, prev_kvs):
        #: Response header.
        self.header: ResponseHeader = ResponseHeader(header)

        #: The number of keys deleted by the delete request.
        self.deleted: int = deleted

        #: The list of deleted key-value pairs matched by the delete range
        #: request, filled when ``prev_kv`` flag was set in the request,
        #: otherwise empty.
        self.prev_kvs = prev_kvs

    def __bool__(self):
        return self.deleted > 0

    def __len__(self):
        return len(self.prev_kvs)

    def __iter__(self):
        for kv in self.prev_kvs:
            yield KeyValue(kv)

    def __getitem__(self, index):
        return KeyValue(self.prev_kvs[index])

    def __repr__(self):
        return (
            f'{self.__class__.__name__}'
            f'[header={self.header!r}, deleted={self.deleted!r}]'
        )


class EventKind(str, enum.Enum):
    #: Designates a ``PUT`` event.
    PUT = 'PUT'

    #: Designates a ``DELETE`` event.
    DELETE = 'DELETE'


class Event(_Slotted):
    """Reperesents a watch event."""

    __slots__ = [
        'kind',
        'kv',
        'prev_kv',
    ]

    def __init__(self, kind, kv, prev_kv=None):
        #: The kind of event. If the type is a ``PUT``, it indicates
        #: new data has been stored to the key. If the type is a ``DELETE``,
        #: it indicates the key was deleted.
        self.kind: EventKind = rpc.Event.EventType.DESCRIPTOR.values_by_number[kind].name

        #: Holds the key-value for the event.
        #: A ``PUT`` event contains current key-value pair.
        #: A ``PUT`` event with version that equals to 1 indicates the creation of a key.
        #: A ``DELETE`` event contains the deleted key with
        #: its modification revision set to the revision of deletion.
        self.kv: KeyValue = KeyValue(kv)

        #: Holds the key-value pair before the event happend.
        self.prev_kv: typing.Optional[KeyValue] = KeyValue(prev_kv) if prev_kv else None


class Watch:
    """Reperesents the result of a watch operation.

    To get emitted events use as an asynchronous iterator, emitted events are
    instances of an :class:`~aetcd.rtypes.Event`.

    Usage example:

    .. code-block:: python

        async for event in client.watch(b'key'):
            print(event)
    """

    def __init__(
        self,
        iterator,
        cancel_func,
        watch_id,
    ):
        self._iterator = iterator
        self._cancel = cancel_func

        #: The ID of the watcher that emits the events.
        self.watch_id: int = watch_id

    def __aiter__(self):
        return self._iterator()

    async def cancel(self):
        """Cancel the watcher so that no more events are emitted."""
        await self._cancel()

    def __repr__(self):
        return f'Watch[watch_id={self.watch_id!r}]'
