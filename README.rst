============
 Docsweeper
============

*Docsweeper* is a linter for version controlled *Python* code bases that finds
potentially outdated docstrings. *Docsweeper* interacts with the version control system
to retrieve a full revision history of a given *Python* source file. For every code
token in the file that has a docstring (see `PEP 257
<https://peps.python.org/pep-0257/>`_), *Docsweeper* will analyze the version control
history to determine

#. in which revision the docstring has last been changed, and
#. how often the source code that is referenced by the docstring has been altered since
   that revision.

This can help you quickly find potentially outdated docstrings in your *Python* code
base.

*Docsweeper* can be used as a stand-alone application or as a plugin for the `Flake8
<https://flake8.pycqa.org/en/latest/>`_ linter.

*Docsweeper* supports the following version control systems:

- `Git <https://git-scm.com/>`_ v1.7.0 or newer, and
- `Mercurial <https://www.mercurial-scm.org/>`_ v5.2 or newer.

Refer to the `documentation <https://docsweeper.readthedocs.io/>`_ for more information.
