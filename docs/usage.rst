=====
Usage
=====

To use ``aetcd3`` in your project:

.. code-block:: python

    import aetcd3

and then create a client:

.. code-block:: python

    etcd = aetcd3.client()

This defaults to ``localhost``, but you can specify any ``host`` and ``port``:

.. code-block:: python

    etcd = etcd3.client(host='etcd-host-01', port=2379)

Values can be stored with the ``put`` method:

.. code-block:: python

    await etcd.put('/key', 'dooot')

You can check this has been stored correctly by testing with ``etcdctl``:

.. code-block:: bash

    $ ETCDCTL_API=3 etcdctl get /key
    /key
    dooot
