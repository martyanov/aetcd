import pytest

import aetcd.client
import aetcd.rpc


def test_auth_with_no_username_or_password():
    with pytest.raises(Exception, match='both username and password'):
        aetcd.client.Client(username='usr')

    with pytest.raises(Exception, match='both username and password'):
        aetcd.client.Client(password='pwd')


def test__build_get_range_request_sort_target():
    key = b'key'
    sort_targets = {
        None: aetcd.rpc.RangeRequest.KEY,
        'key': aetcd.rpc.RangeRequest.KEY,
        'version': aetcd.rpc.RangeRequest.VERSION,
        'create': aetcd.rpc.RangeRequest.CREATE,
        'mod': aetcd.rpc.RangeRequest.MOD,
        'value': aetcd.rpc.RangeRequest.VALUE,
    }

    for sort_target, expected_sort_target in sort_targets.items():
        range_request = aetcd.client.Client._build_get_range_request(
            key,
            sort_target=sort_target,
        )
        assert range_request.sort_target == expected_sort_target

    with pytest.raises(ValueError):
        aetcd.client.Client._build_get_range_request(key, sort_target='unknown')


def test__build_get_range_request_sort_order():
    key = b'key'
    sort_orders = {
        None: aetcd.rpc.RangeRequest.NONE,
        'ascend': aetcd.rpc.RangeRequest.ASCEND,
        'descend': aetcd.rpc.RangeRequest.DESCEND,
    }

    for sort_order, expected_sort_order in sort_orders.items():
        range_request = aetcd.client.Client._build_get_range_request(
            key,
            sort_order=sort_order,
        )
        assert range_request.sort_order == expected_sort_order

    with pytest.raises(ValueError):
        aetcd.client.Client._build_get_range_request(key, sort_order='unknown')


def test__ops_to_requests():
    with pytest.raises(Exception):
        aetcd.client.Client._ops_to_requests(['not_transaction_type'])

    with pytest.raises(TypeError):
        aetcd.client.Client._ops_to_requests(0)


def test_compare_version():
    key = 'key'
    tx = aetcd.client.Transactions()

    version_compare = tx.version(key) == 1
    assert version_compare.op == aetcd.rpc.Compare.EQUAL

    version_compare = tx.version(key) != 2
    assert version_compare.op == aetcd.rpc.Compare.NOT_EQUAL

    version_compare = tx.version(key) < 91
    assert version_compare.op == aetcd.rpc.Compare.LESS

    version_compare = tx.version(key) > 92
    assert version_compare.op == aetcd.rpc.Compare.GREATER
    assert version_compare.build_message().target == aetcd.rpc.Compare.VERSION


def test_compare_value():
    key = 'key'
    tx = aetcd.client.Transactions()

    value_compare = tx.value(key) == 'b'
    assert value_compare.op == aetcd.rpc.Compare.EQUAL

    value_compare = tx.value(key) != 'b'
    assert value_compare.op == aetcd.rpc.Compare.NOT_EQUAL

    value_compare = tx.value(key) < 'b'
    assert value_compare.op == aetcd.rpc.Compare.LESS

    value_compare = tx.value(key) > 'b'
    assert value_compare.op == aetcd.rpc.Compare.GREATER
    assert value_compare.build_message().target == aetcd.rpc.Compare.VALUE


def test_compare_mod():
    key = 'key'
    tx = aetcd.client.Transactions()

    mod_compare = tx.mod(key) == -100
    assert mod_compare.op == aetcd.rpc.Compare.EQUAL

    mod_compare = tx.mod(key) != -100
    assert mod_compare.op == aetcd.rpc.Compare.NOT_EQUAL

    mod_compare = tx.mod(key) < 19
    assert mod_compare.op == aetcd.rpc.Compare.LESS

    mod_compare = tx.mod(key) > 21
    assert mod_compare.op == aetcd.rpc.Compare.GREATER
    assert mod_compare.build_message().target == aetcd.rpc.Compare.MOD


def test_compare_create():
    key = 'key'
    tx = aetcd.client.Transactions()

    create_compare = tx.create(key) == 10
    assert create_compare.op == aetcd.rpc.Compare.EQUAL

    create_compare = tx.create(key) != 10
    assert create_compare.op == aetcd.rpc.Compare.NOT_EQUAL

    create_compare = tx.create(key) < 155
    assert create_compare.op == aetcd.rpc.Compare.LESS

    create_compare = tx.create(key) > -12
    assert create_compare.op == aetcd.rpc.Compare.GREATER
    assert create_compare.build_message().target == aetcd.rpc.Compare.CREATE
