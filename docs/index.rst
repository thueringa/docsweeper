======================================
Welcome To Docsweeper's Documentation!
======================================

*Docsweeper* is a linter for version controlled *Python* code bases that finds
potentially outdated docstrings in your source files. For every code token in the file
that has a docstring (see :pep:`257`), *Docsweeper* will interact with your *Git* or
*Mercurial* version control system to determine:

#. in which revision the docstring has last been changed, and
#. how often the source code that is referenced by the docstring has been altered since
   that revision.

Used as a :ref:`stand-alone application <usage_cmdline>` or as a :ref:`plugin
<usage_plugin>` for the `Flake8 <https://flake8.pycqa.org/en/latest/>`_ linter,
*Docsweeper* can be integrated into your code check-in or linting process easily and
help you quickly determine which docstrings potentially contain obsolete information.

Compatibility
=============

*Docsweeper* supports Linux, Mac, and Windows platforms that are compatible with Python
3.7 or newer. In addition to a working Python installation, you will also need at least
one of the version control systems you intend to use *Docsweeper* with:

#. `Git <https://git-scm.com/>`_ v1.7.0 or newer, and/or
#. `Mercurial <https://www.mercurial-scm.org/>`_ v5.2 or newer. This is the the first
   release of *Mercurial* with `official support
   <https://www.mercurial-scm.org/wiki/Python3>`_ for *Python* 3.

Installation
============

In addition to a working Python v3.7+ environment, the following additional packages are
required as well:

- `click <https://click.palletsprojects.com/en/8.1.x/>`_ v8.1.0 or newer.

*Docsweeper* is available on `PyPI <https://pypi.org/project/docsweeper/>`_. Install it
with `pip <https://pip.pypa.io/>`_ to take care of dependencies automatically:

.. code-block:: console

   $ pip install docsweeper

After installation, see section :ref:`usage` for instructions on how to configure and
run *Docsweeper* on your code base.

Documentation Contents
======================

.. toctree::
   :maxdepth: 2

   Overview and Installation <self>
   usage
   reference

.. toctree::
   :maxdepth: 1

   developer
   changelog

Related Projects
================

`Darglint <https://github.com/terrencepreilly/darglint>`_
    A linter that checks whether a docstring exists, whether it is well-formed, and if
    its definitions match the implementation.
`pydocstyle <https://github.com/pycqa/pydocstyle>`_
    A linter that checks for compliance of docstrings with *Python* docstring conventions.
`flake8-docstrings <https://github.com/pycqa/flake8-docstrings>`_
    A *Flake8* plugin for integration of *pydocstyle* with *Flake8*.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
