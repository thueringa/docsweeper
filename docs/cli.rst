
.. _usage_cmdline:

=====================================
Invoking Docsweeper From Command Line
=====================================

A list of available version control system interfaces and their default
executable locations is printed at the end of the command line help:

.. code-block:: console

   $ docsweeper -h

For example, to analyze the source file :file:`source.py` in a git repository, run:

.. code-block:: console

   $ docsweeper --vcs git source.py

If the default executable location for your version control system is not correct for
your system, override it using :code:`--vcs-executable` option or a :ref:`configuration
file <file_config>`:

.. code-block:: console

   $ docsweeper --vcs git --vcs-executable /path/to/git source.py

.. _cmdline_spec:

Full Command Line Reference
===========================

.. note::

    This command line reference is also available by running ``docsweeper -h``.


Usage: ``docsweeper [OPTIONS] FILE...``

Analyze ``FILE`` or multiple ``FILEs`` for outdated docstrings.

Options:
  --vcs VCS
                             .. note::

                                This command line option was introduced in v1.2.0.

                             History of FILEs will be retrieved using the
                             version control system ``VCS``.

                             Supported values for ``VCS``: ``git`` *|* ``hg``

                             Default value: ``git``
  -e, --vcs-executable PATH  the version control executable located at ``PATH``
                             will be used during analysis.
  --no-follow-rename         Do not follow renames of files.
  -c, --config PATH          Load a Docsweeper configuration file located at
                             ``PATH``.
  -v, --verbose              Set verbose mode.
  -d, --debug                Set debugging mode. Lots of messages.

  -V, --version              Show version information.
  -h, --help                 Show command line reference.

Configuration of stand-alone application
========================================

The stand-alone version of *Docsweeper* is configured independently of the *Flake8*
plugin via :ref:`command line parameters <cmdline_spec>` or using a configuration file.
Command line options always take precedence over values in a configuration file.


.. _file_config:

Configuration Via File
~~~~~~~~~~~~~~~~~~~~~~

If ``Docsweeper`` is passed the command line option ``--config`` or ``-c`` followed by
the path of a `configuration file
<https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_, it
will try to load configuration values from this file. The following example shows all
configuration sections and the options they support:

[docsweeper] :
    Configuration section for general options.

    vcs : ``git`` *|* ``hg``
        Choose the type of version control system.

        Default value ``git``
    follow_rename : ``true`` *|* ``false``
        Follow version control history along renames of files.

        Default value: ``true``
[docsweeper.git] :
    Configuration section for *git*.

    executable : *string*
        Path of the *git* executable.

        Default value: see the output of ``docsweeper -h``
[docsweeper.hg] :
    Configuration section for *Mercurial*.

    executable : *string*
        Path of the *Mercurial* executable.

        Default value: see the output of ``docsweeper -h``


.. code-block:: ini

   [docsweeper]
   vcs = git
   follow_rename = True

   [docsweeper.git]
   executable = /usr/bin/git

   [docsweeper.hg]
   executable = /usr/bin/hg
