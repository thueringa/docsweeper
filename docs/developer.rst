===========================
 Developing For Docsweeper
===========================

This document contains instructions about how to obtain a functioning development
environment of *Docsweeper*, and how new additions to the code base can be tested.

*Docsweeper* uses `Poetry
<https://python-poetry.org/>`_ for dependency management and `tox
<https://tox.wiki/en/latest/>`_ for automation testing and linting.

Installing The Package
======================

Clone the *Docsweeper* `Github repository <https://github.com/thueringa/docsweeper>`_,
and install the project environment by running the following command in the repository
root:

.. code-block:: console

   $ git checkout https://github.com/thueringa/docsweeper.git
   $ cd docsweeper
   $ poetry install


Running The Test Suite
======================

There is a test suite that tests the correct behavior of *Docsweeper* using all
installed supported version control systems with different test repositories. Tests can
also be run with an additional supplied *git* or *hg* executable, for example to test
behavior of *Docsweeper* with old versions.

Test Configuration
------------------

To run the tests successfully, you may need to adjust the paths of your version control
executables. You can do so in a section named ``docsweeper`` in the file ``pytest.ini``,
located in the repository root. Supported options are:

[docsweeper] :
    Configuration section for *Docsweeper*.

    git_executable : *string*
        location of *git* executable on your system.

    hg_executable : *string*
        Location of *Mercurial* executable on your system.

    old_git_executable : *string*
        Location of an alternative *git* executable for tests with older versions. This
        setting is ignored if tests are run with the ``--no-old-git`` parameter.

    old_hg_executable : *string*
        Location of an alternative *Mercurial* executable for tests with older versions.
        This setting is ignored if tests are run with the ``--no-old-hg`` parameter.

For example, put the following snippet in your ``pytest.ini`` to change the *git*
executable to ``/usr/sbin/git``:

.. code-block:: ini

   [docsweeper]
   git_executable = /usr/sbin/git


Running The Tests
-----------------

Having properly configured your executable paths, you should be able to run the tests by
invoking `pytest` through `poetry` using the previously installed environment. Run the
following command in the repository root:

.. code-block:: console

   $ poetry run pytest

You can also test *Docsweeper* on a specific *Python* version by using one of the test
environments provided in :file:`tox.ini`. For example, to run the test suite with
*Python* 3.9, invoke:

.. code-block:: console

   $ poetry run tox -e py39-test

Currently supported *Python* environments are :code:`py37`, :code:`py38`, :code:`py39`,
and :code:`py310`. Refer to the file :file:`tox.ini` in the repository root directory
for all available test and linter environments.

Available Test Suites
---------------------

Specific tests can be added or omitted from the test suite by passing any combination of
the following parameters to a test run:

--no-old-git  Do not run tests that use the old git version.
--no-old-hg  Do not run tests that use the old *Mercurial* version.

For example, invoke the following command to omit the old *git* version tests:

.. code-block:: console

   $ poetry run pytest --no-old-git

Running The Pre-Commit Script
=============================

A comprehensive pre-commit script is provided in ``tox.ini``. It performs style and type
checking, as well as running the test suite on all supported *Python* environments. Run
it by calling

.. code-block:: console

   $ poetry run tox -e pre-commit

Running The Profiling Suite
===========================

*Docsweeper* provides a simple :py:mod:`cProfile` test suite. From the repository root,
run the :code:`profiler` test module in the :file:`src/tests` directory:

.. code-block:: console

   $ poetry run python -m tests.profiler

Upon execution, the module prints an overview of the most resource-intensive functions
of *Docsweeper*. To perform a manual review of the profiler statistics, run the command
with an additional :code:`-i` flag and inspect the :code:`stats` variable, which is an
instance of :class:`pstats.Stats`.

Creating Documentation
======================

To let `Sphinx* <https://www.sphinx-doc.org/en/master/>`_ create HTML documentation in
:file:`docs/html`, invoke `poetry run tox -e docs`. It is recommended to use *Sphinx*
v4.5.0 to create the docs, which is only installed for enviroments with *Python* >=
v3.10. Above-mentioned command will choose the correct *Python* version automatically,
if there is one in ``PATH``.

Commit Checklist
================

Before merging code into ``master``, verify the following conditions:

#. If any new code has been introduced: is it documented in source code? If it is
   public, is it properly documented in the *sphinx* documentation?
#. Does the command ``poetry run tox -e pre-commit`` return successfully? If not, fix
   the issues. Run ``poetry run tox -e fix-style`` for fixing style issues automatically
   where possible.
#. Has :file:`changelog.md` been updated? Add the changes to the development version on
   top of the document and change the version number accordingly.
#. Bump the version number in :file:`pyproject.toml` if necessary.
