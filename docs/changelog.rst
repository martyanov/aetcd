=========
Changelog
=========

0.1.0a7 (2021-04-29)
--------------------

Internals
^^^^^^^^^

* Update proto files from upstream etcd 4.3.15
* Move proto files out of aetcd3 package
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
