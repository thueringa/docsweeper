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

*Docsweeper* uses `Semantic Versioning <https://semver.org/>`_. A new PATCH release
(x.y.\ **z**) contains only backwards-compatible bugfixes, a new MINOR release
(x.\ **y**\.z) adds backwards-compatible functionality, and a new MAJOR release
(**x**.y.y) introduces incompatible API changes.

v2.0.0 (in development)
=======================

Incompatible Changes
--------------------

- drop :ref:`command line option <cmdline_spec>` ``--vcs-shim``. Is replaced by command line
  option ``-vcs``.

Upgrading from Docsweeper v1.x
------------------------------

- Replace usage of command line option ``--vcs-shim`` with ``--vcs``. Parameter
  signature of ``--vcs`` option is unchanged from ``--vcs-shim``.

v1.2.5 (in development)
=======================

Bugfixes
--------

- fix crash when following renames using mercurial version control systems

v1.2.4 (released May 19, 2022)
==============================

Bugfixes
--------

- fix bug introduced in v1.2.1 that caused crash if input file was not
  parseable at some point in version control history

Miscellaneous
-------------
- improve error messages for CLI users

v1.2.3 (released May 17, 2022)
==============================

Miscellaneous
-------------
- fix rst rendering error in changelog

v1.2.2 (released May 17, 2022)
==============================

Bugfixes
--------

- fix Windows build

v1.2.1 (released May 14, 2022)
==============================

Dependencies
------------

- drop dependency on ``typing_extensions`` for Python 3.7

Miscellaneous
-------------

- improve error handling

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
