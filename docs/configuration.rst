Configuration
=============

.. _flake8_config:

Configuration Of Docsweeper As A Flake8 Plugin
----------------------------------------------

The *Flake8* plugin can be configured via a configuration section in the `Flake8
configuration file
<https://flake8.pycqa.org/en/latest/user/configuration.html#configuration-locations>`_
or by passing specific command line options to the ``flake8`` command.

.. important:: The *Flake8* plugin is disabled by default. Add ``DOC100`` to your
   enabled extensions in your *Flake8* configuration to use it:

   .. code-block:: ini

      [flake8]
      enable-extensions=DOC100

.. _flake8_file_config:

Plugin Configuration In The Flake8 Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following options are respected by *Docsweeper* if set by the user:

``max_changes`` : *integer*
    Amount of code changes that are allowed since the last docstring update before
    :ref:`code violation DOC100 <DOC100>` triggers.

    Default value: ``0``
``no_follow_rename`` : ``true`` *|* ``false``
    Follow version control history along renames of files.

    Default value: ``false``
``vcs`` : *string*
    Version control system that is used. Currently supported values are ``git`` and
    ``hg``.

    Default value: ``git``
``vcs_executable`` : *string*
    Location of the version control system executable.

    Default value: see the output of ``docsweeper -h``

Plugin Configuration With Command Line Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command line options are available:

.. _max_changes:

--max-changes MAX_CHANGES  :ref:`Code violation DOC100 <DOC100>` triggers when more
                           than ``MAX_CHANGES`` changes to the source code have been
                           made since the last docstring change.
--no-follow-rename         Follow version control history along renames of files.
--vcs VCS_TYPE             ``VCS_TYPE`` is the type of version control system used.

                           Allowed values: ``git|hg``
--vcs-executable VCS_EXECUTABLE
    The version control system located at ``VCS_EXECUTABLE`` will be used.

Using Docsweeper As A Standalone Application
--------------------------------------------

The stand-alone version of *Docsweeper* can be configured independently of the *Flake8*
plugin via :ref:`command line parameters <usage_cmdline>` or using a configuration file.
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
