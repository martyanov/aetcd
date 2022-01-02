Python asyncio-based client for etcd
====================================

.. image:: https://github.com/martyanov/aetcd/workflows/build/badge.svg?branch=master
   :alt: Build Status
   :target: https://github.com/martyanov/aetcd/actions

.. image:: https://codecov.io/gh/martyanov/aetcd/branch/master/graph/badge.svg
   :alt: Coverage report
   :target: https://codecov.io/gh/martyanov/aetcd/branch/master

.. image:: https://img.shields.io/badge/docs-aetcd.rtfd.io-green.svg
   :alt: Documentation
   :target: https://aetcd.readthedocs.io

.. image:: https://img.shields.io/pypi/v/aetcd.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/aetcd

.. image:: https://img.shields.io/pypi/pyversions/aetcd.svg
   :alt: Supported Python Versions
   :target: https://pypi.python.org/pypi/aetcd

.. image:: https://img.shields.io/github/license/martyanov/aetcd
   :alt: License
   :target: https://github.com/martyanov/aetcd/blob/master/LICENSE

Installation
~~~~~~~~~~~~

.. code-block:: bash

    $ python -m pip install aetcd

Basic usage
~~~~~~~~~~~

Run ``asyncio`` REPL:

.. code-block:: bash

    $ python -m asyncio

Test the client:

.. code-block:: python

    import aetcd

    async with aetcd.Client() as client:
        await client.put(b'foo', b'bar')
        await client.get(b'foo')
        await client.delete(b'foo')

Acknowledgements
~~~~~~~~~~~~~~~~

This project is a fork of `etcd3aio`_, which itself is a fork
of `python-etcd3`_. ``python-etcd3`` was originally written by `kragniz`_. ``asyncio`` suppport
was contributed by `hron`_ and based on the previous work by `gjcarneiro`_. Many thanks to all
the `people`_ involved in the project.

.. _etcd3aio: https://github.com/hron/etcd3aio
.. _python-etcd3: https://github.com/kragniz/python-etcd3
.. _kragniz: https://github.com/kragniz
.. _hron: https://github.com/hron
.. _gjcarneiro: https://github.com/gjcarneiro
.. _people: https://github.com/martyanov/aetcd/graphs/contributors
