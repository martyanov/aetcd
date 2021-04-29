.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways.

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/martyanov/aetcd3/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with ``bug``
and ``help wanted`` is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with ``enhancement``
and ``help wanted`` is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

``aetcd3`` could always use more documentation, whether as part of the
official ``aetcd3`` docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/martyanov/aetcd3/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome! :)

Get Started!
------------

Ready to contribute? Here's how to set up ``aetcd3`` for local development.

1. Fork the ``aetcd3`` repo on GitHub.

2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/aetcd3.git

3. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

5.  Make your changes locally.

6. When you're done making changes, check that your changes pass lint and tests for all the supported Python versions::

    $ make PYTHON_BIN=python3.9 lint
    $ make PYTHON_BIN=python3.9 test

7. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -S -m "Your detailed description of your changes"
    $ git push origin name-of-your-bugfix-or-feature

8. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should work for Python 3.8+. Check
   https://github.com/martyanov/aetcd3/actions
   and make sure that the pipelines pass for all supported Python versions.

Generating protobuf stubs
-------------------------

If the upstream protobuf files change, you can update ``.proto`` files and generate new stubs::

    $ make genproto


Cutting new releases
--------------------

The release process to PyPi is automated using GitHub Actions.

1. Check changes since the last release:

   .. code-block:: bash

       $ git log $(git describe --tags --abbrev=0)..HEAD --oneline

2. Bump the version (respecting semver, one of ``major``, ``minor`` or
   ``patch``):

   .. code-block:: bash

       $ git tag -s -a v<version> -m "Release version <version>"

3. Push to github:

   .. code-block:: bash

       $ git push
       $ git push --tags

4. Wait for GitHub Actions jobs to run and deploy to PyPI.
