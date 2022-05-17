============
 Docsweeper
============

.. image:: https://img.shields.io/pypi/pyversions/docsweeper?style=flat-square
   :alt: PyPI - Python Version
   :target: https://pypi.org/project/docsweeper/

.. image:: https://img.shields.io/pypi/v/docsweeper?style=flat-square
   :alt: PyPI
   :target: https://pypi.org/project/docsweeper/

.. image:: https://img.shields.io/pypi/l/docsweeper?style=flat-square
   :alt: PyPI - License
   :target: https://pypi.org/project/docsweeper/

.. image:: https://readthedocs.org/projects/docsweeper/badge/?version=stable&style=flat-square
   :target: https://docsweeper.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status

.. image:: https://img.shields.io/travis/com/thueringa/docsweeper?style=flat-square
   :alt: Travis (.com)
   :target: https://app.travis-ci.com/github/thueringa/docsweeper

.. image:: https://img.shields.io/appveyor/build/AndreasThring/docsweeper
   :alt: AppVeyor
   :target: https://ci.appveyor.com/project/AndreasThring/docsweeper

*Docsweeper* is a linter for version controlled *Python* code bases that finds
potentially outdated docstrings in your source files. For every code token in the file
that has a docstring (see `PEP 257 <https://peps.python.org/pep-0257/>`_), *Docsweeper*
will interact with your *Git* or *Mercurial* version control system to determine:

#. in which revision the docstring has last been changed, and
#. how often the source code that is referenced by the docstring has been altered since
   that revision.

Used as a stand-alone application or as a plugin for the `Flake8
<https://flake8.pycqa.org/en/latest/>`_ linter, *Docsweeper* can be integrated into your
code check-in or linting process easily and help you quickly determine which docstrings
potentially contain obsolete information.

Compatibility
=============

*Docsweeper* supports Linux, Mac, and Windows platforms that are compatible with Python
3.7 or newer. In addition to a working Python installation, you will also need at least
one of the version control systems you intend to use *Docsweeper* with:

#. `Git <https://git-scm.com/>`_ v1.7.0 or newer, and/or
#. `Mercurial <https://www.mercurial-scm.org/>`_ v5.2 or newer. This is the the first
   release of *Mercurial* with `official support
   <https://www.mercurial-scm.org/wiki/Python3>`_ for *Python* 3.


Refer to the `documentation <https://docsweeper.readthedocs.io/>`_ for more information.
