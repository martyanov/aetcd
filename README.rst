Python asyncio-based client for etcd
====================================

.. image:: https://github.com/martyanov/aetcd3/workflows/build/badge.svg?branch=master
   :alt: Build Status
   :target: https://github.com/martyanov/aetcd3/actions

.. image:: https://codecov.io/gh/martyanov/aetcd3/coverage.svg?branch=master
   :alt: Coverage report
   :target: https://codecov.io/gh/martyanov/aetcd3/branch/master

.. image:: https://img.shields.io/badge/docs-aetcd3.rtfd.io-green.svg
   :alt: Documentation
   :target: https://aetcd3.readthedocs.io

.. image:: https://img.shields.io/pypi/v/aetcd3.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/aetcd3

.. image:: https://img.shields.io/pypi/pyversions/aetcd3.svg
   :alt: Supported Python Versions
   :target: https://pypi.python.org/pypi/aetcd3

.. image:: https://img.shields.io/github/license/martyanov/aetcd3
   :alt: License
   :target: https://github.com/martyanov/aetcd3/blob/master/LICENSE

Installation
~~~~~~~~~~~~

.. code:: bash

    $ python3 -m pip install aetcd3

Basic usage
~~~~~~~~~~~

.. code-block:: python

    import aetcd3

    client = aetcd3.client()

    await client.put('foo', 'bar')
    await client.get('foo')
    await client.delete('foo')

Acknowledgements
~~~~~~~~~~~~~~~~

This project is a fork of `etcd3aio`_, which itself is a fork
of `python-etcd3`_. ``python-etcd3`` was originally written by `kragniz`_. ``asyncio`` suppport
was contributed by `hron`_ and based on the previous work by `gjcarneiro`_. Kudos to all
the people involved in the project.

.. _grpclib: https://github.com/vmagamedov/grpclib
.. _etcd3aio: https://github.com/hron/etcd3aio
.. _python-etcd3: https://github.com/kragniz/python-etcd3
.. _kragniz: https://github.com/kragniz
.. _hron: https://github.com/hron
.. _gjcarneiro: https://github.com/gjcarneiro
