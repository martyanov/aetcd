=====
Usage
=====

To use ``aetcd3`` in your project:

.. code-block:: python

    import aetcd3

and then create a client:

.. code-block:: python

    client = aetcd3.client()

This defaults to ``localhost``, but you can specify any ``host`` and ``port``:

.. code-block:: python

    client = aetcd3.client(host='etcd-host-01', port=2379)


Values
======

Values can be stored with the ``put`` method:

.. code-block:: python

    await client.put('foo', 'bar')

You can check this has been stored correctly:

.. code-block:: python

    await client.get('foo')

Or by testing with ``etcdctl``:

.. code-block:: bash

    $ ETCDCTL_API=3 etcdctl get foo
    foo
    bar

You can delete previously set value:

.. code-block:: python

    await client.delete('foo')

Locks
=====

You can use locks API directly:

.. code-block:: python

    lock = client.lock('foo')

    await lock.acquire()
    # Do something
    await lock.release()


Or as a context manager:

.. code-block:: python

    async with client.lock('foo') as lock:
        # Do something

Transactions
============

.. code-block:: python

    await client.transaction(
        compare=[
            client.transactions.value('foo') == 'bar',
            client.transactions.version('foo') > 0,
        ],
        success=[
            client.transactions.put('foo', 'success'),
        ],
        failure=[
            client.transactions.put('foo', 'failure'),
        ],
    )

Watch
=====

Watch for key:

.. code-block:: python

    watch_count = 0
    events_iterator, cancel = await client.watch('foo')

    async for event in events_iterator:
        print(event)
        watch_count += 1
        if watch_count > 10:
            await cancel()

Watch for key prefix:

.. code-block:: python

    watch_count = 0
    events_iterator, cancel = await client.watch_prefix('foo')

    async for event in events_iterator:
        print(event)
        watch_count += 1
        if watch_count > 10:
            await cancel()

Receive watch events via a callback function:

.. code-block:: python

    def watch_callback(event):
        print(event)

    watch_id = await client.add_watch_callback('foo', watch_callback)

Cancel watch:

.. code-block:: python

    await client.cancel_watch(watch_id)
