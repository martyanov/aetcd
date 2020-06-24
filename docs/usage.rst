=========
API Usage
=========

To use aetcd3 in a project:

.. code-block:: python

    import aetcd3

and create a client:

.. code-block:: python

    etcd = aetcd3.client()

This defaults to localhost, but you can specify the host and port:

.. code-block:: python

    etcd = etcd3.client(host='etcd-host-01', port=2379)

Putting values into etcd
------------------------

Values can be stored with the ``put`` method:

.. code-block:: python

    await etcd.put('/key', 'dooot')

You can check this has been stored correctly by testing with etcdctl:

.. code-block:: bash

    $ ETCDCTL_API=3 etcdctl get /key
    /key
    dooot

API
===

.. autoclass:: aetcd3.Etcd3Client
    :members:

.. autoclass:: aetcd3.Member
    :members:

.. autoclass:: aetcd3.Lease
    :members:

.. autoclass:: aetcd3.Lock
    :members:
