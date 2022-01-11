import aetcd


def test_module_export_classes():
    module_attrs_all = set(aetcd.__all__)
    module_attrs_exported = set(attr for attr in dir(aetcd) if attr[0].isupper())
    assert module_attrs_all == module_attrs_exported
