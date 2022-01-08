==========
User guide
==========

To use ``aetcd`` in your project:

.. code-block:: python

    import aetcd

and then create a client:

.. code-block:: python

    client = aetcd.Client()

This defaults to ``localhost``, but you can specify any ``host`` and ``port``:

.. code-block:: python

    client = aetcd.Client(host='etcd', port=2379)

Don't forget to close the client after use:

.. code-block:: python

    await client.close()

You can also use the client as a context manager:

.. code-block:: python

    async with aetcd.Client() as client:
        # Do something


Values
======

Values can be stored with the ``put`` method:

.. code-block:: python

    await client.put(b'key', b'value')

You can check this has been stored correctly:

.. code-block:: python

    await client.get(b'key')

Or by testing with ``etcdctl``:

.. code-block:: bash

    $ ETCDCTL_API=3 etcdctl get key
    key
    value

You can delete previously set value:

.. code-block:: python

    await client.delete(b'key')

Watch
=====

Watch for key:

.. code-block:: python

    watch_count = 0
    watch = await client.watch(b'key')

    async for event in watch:
        print(event)
        watch_count += 1
        if watch_count > 10:
            await watch.cancel()

Watch for key prefix:

.. code-block:: python

    watch_count = 0
    watch = await client.watch_prefix(b'key')

    async for event in watch:
        print(event)
        watch_count += 1
        if watch_count > 10:
            await watch.cancel()

Locks
=====

You can use locks API directly:

.. code-block:: python

    lock = client.lock(b'key')

    await lock.acquire()
    # Do something
    await lock.release()


Or as a context manager:

.. code-block:: python

    async with client.lock(b'key') as lock:
        # Do something

Transactions
============

.. code-block:: python

    await client.transaction(
        compare=[
            client.transactions.value(b'key') == b'value',
            client.transactions.version(b'key') > 0,
        ],
        success=[
            client.transactions.put(b'key', b'success'),
        ],
        failure=[
            client.transactions.put(b'key', b'failure'),
        ],
    )
