=========
Changelog
=========

1.0.0a4 (2023-05-24)
--------------------

Dependencies
^^^^^^^^^^^^

* Remove pifpaf from dependencies

1.0.0a3 (2023-05-24)
--------------------

Improvements
^^^^^^^^^^^^

* Use monotonic timer in locks implementation
* Limit client connect and close waiting time
* Support lease in replace operation (#21)
* Replace sync subprocess call with async version (#25)
* Add UnauthenticatedError
* Add Python 3.11 support
* Add duplicate lease exception (#22)
* Add 3.4 and 3.5 ETCD versions to CI matrix (#26)
* Set timeout for tests job on CI (#27)
* Add keepalive ETCD client settings in integration tests (#28)
* Fix test for serializable read

Bugfixes
^^^^^^^^

* Fix Connect and Watch iterator

Dependencies
^^^^^^^^^^^^

* Bump packaging dependencies: pip 23.0, setuptools 67.3.2, wheel 0.38.4
* Bump twine to 4.0.2
* Bump flake8 to 6.0.0 and update related plugins
* Bump pytest-asyncio to 0.20.3
* Bump pytest to 7.2.1
* Bump pytest-cov to 4.0.0
* Bump pytest-mock to 3.10.0
* Bump sphinx to 6.1.3 and sphinx_rtd_theme to 1.2.0
* Bump grpcio to 1.51.1 and protobuf to 4+

1.0.0a2 (2022-01-14)
--------------------

Features
^^^^^^^^

* ``grpclib`` was replaced with ``grpc.aio``
* Now the API are only accepting bytes
* Get, put, delete and watch operations are wrapped into friendlier result types
* Implementation of ``delete_range`` method (`#14 <https://github.com/martyanov/aetcd/pull/14>`_)
* All ``grpc`` exceptions are now wrapped by ``ClientError``
* Locking implementation is now in-sync with upstream version
* Add Python 3.10 support

Bugfixes
^^^^^^^^

* Fix ``client.watch()`` raising ``ConnectionTimeoutError`` errors on client timeout (`#13 <https://github.com/martyanov/aetcd/pull/13>`_)
* Correctly shutdown the watcher on RPC stream termination

Documentation
^^^^^^^^^^^^^

* The project documentation was reorganized, all API types and methods are now on a single page
* Many methods and types were documented, in sync with ``etcd`` documentation

Dependencies
^^^^^^^^^^^^

* The only runtime dependencies now are ``grpcio`` and ``protobuf``

Internals
^^^^^^^^^

* Tests were refactored into separate modules divided into two groups: unit and integration
* Use the latest upstream version of ``etcd`` for tests, instead of a system-packaged one
* Fixed broken tests
* Removed dead code


1.0.0a1 (2021-12-26)
--------------------

API changes
^^^^^^^^^^^

* Rename the package to aetcd
* Remove client helper and rename ``Etcd3Client`` to ``Client``
* Rename ``Client.open`` to ``Client.connect``, this is a more appropriate name
* Refactor exception names and provide them via base package imports, see the docs for details

Internals
^^^^^^^^^

* Bump the project dependencies
* Update proto files from upstream etcd 3.5.1

0.1.0a7 (2021-04-29)
--------------------

Internals
^^^^^^^^^

* Update proto files from upstream etcd 4.3.15
* Move proto files out of aetcd package
* Improved documentation
* Setup quotes and import linting
* Code cleanup

0.1.0a6 (2021-04-27)
--------------------

Internals
^^^^^^^^^

* Build packages only on the latest supported python version

0.1.0a5 (2021-04-27)
--------------------

Bugfixes
^^^^^^^^

* Await for stream end

Internals
^^^^^^^^^

* Support for aiofiles 0.6.x
* Bump setup dependencies: pip 21.1, setuptools 56.0.0
* Bump test dependencies: pytest 6.2.3, pytest-asyncio 0.15.1
* Bump dev dependencies: flake8 3.9.1, grcpio-tools 1.37.0
* Get rid of tox
* Manage everything via provided Makefile, use CI to upload tagged packages

0.1.0a4 (2021-03-26)
--------------------

* Bump setuptools_scm to 0.6.1

0.1.0a3 (2021-03-26)
--------------------

* Bump grpclib version ranges to fix incompatibility with h2
* Bump packaging, dev and test dependencies to recent versions
* Get rid of python 3.7 support


0.1.0a2 (2020-06-22)
--------------------

* Add Python 3.7 support
* Coverage reports
* Run tests on CI

0.1.0a1 (2020-06-09)
--------------------

* First release on PyPI.
