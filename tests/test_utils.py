import aetcd.utils


def test_prefix_range_end():
    assert aetcd.utils.prefix_range_end(b'foo') == b'fop'
    assert aetcd.utils.prefix_range_end(b'ab\xff') == b'ac\xff'
    assert aetcd.utils.prefix_range_end(
        b'a\xff\xff\xff\xff\xff') == b'b\xff\xff\xff\xff\xff'


def test_to_bytes():
    assert isinstance(aetcd.utils.to_bytes(b'key'), bytes) is True
    assert isinstance(aetcd.utils.to_bytes('key'), bytes) is True
    assert aetcd.utils.to_bytes(b'key') == b'key'
    assert aetcd.utils.to_bytes('key') == b'key'
