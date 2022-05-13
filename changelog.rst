===========
 Changelog
===========
..
    Template:

    vX.X.X (released XXX XX, XXXX)
    ==============================

    Dependencies
    ------------

    Incompatible Changes
    --------------------

    Deprecations
    ------------

    New Features
    ------------

    Bugfixes
    --------

    Miscellaneous
    -------------

v2.0.0 (in development)
=======================

Incompatible Changes
--------------------

- drop `command line option <cmdline_spec>` ``--vcs-shim``. Is replaced by command line
  option ``-vcs``.

Upgrading from Docsweeper v1.x
------------------------------

- Replace usage of command line option ``--vcs-shim`` with ``--vcs``. Parameter
  signature of this option is unchanged from ``--vcs-shim``.

v1.2.1 (in development)
=======================

Dependencies
------------

- drop dependency on ``typing_extensions`` for Python 3.7

v1.2.0 (released May 11, 2022)
==============================

Dependencies
------------

- drop support for *Python* 3.11 environments. Was enabled accidentally due to build
  configuration error, and will be reinstated when *Python* 3.11 is officially released.

Deprecations
------------

- command line option ``--vcs-shim``. Use command line option ``--vcs`` that was
  introduced in this version instead.

New Features
------------

- introduce ``--vcs`` command line option.

v1.1.0 (released May 10, 2022)
==============================

New Features
------------

- introduce ``-V``/``--version`` command line option

Bugfixes
--------

- fix incompatibility with *git* v2.36

Miscellaneous
-------------

- change options for test runner

v1.0.1 (released May 09, 2022)
==============================

Bugfixes
--------

- enable editable installs

v1.0.0 (released May 09, 2022)
==============================

Initial public release of *Docsweeper*.
