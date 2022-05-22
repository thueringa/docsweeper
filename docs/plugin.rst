.. _usage_plugin:

=====================================
 Using Docsweeper As A Flake8 Plugin
=====================================

Upon installation, *Docsweeper* will register itself automatically as a plugin for
*Flake8* if it is installed. See :ref:`configuration instructions <flake8_config>` for
instructions on how to configure the plugin.

Error/Violation Codes
=====================

*Docsweeper* employs the following *Flake8* error codes:

.. _DOC100:

DOC100 Potentially Outdated Docstring
-------------------------------------

The code of this token has changed more times than allowed since the docstring that
references it has been updated.

The amount of allowed code changes until this violation triggers is determined by the
``--max_changes`` :ref:`command line option <max_changes>` or ``max_changes``
option in the :ref:`Flake8 configuration file <flake8_file_config>`.

.. _flake8_config:

Configuration Of Docsweeper As A Flake8 Plugin
==============================================

The *Flake8* plugin can be configured via a configuration section in the `Flake8
configuration file
<https://flake8.pycqa.org/en/latest/user/configuration.html#configuration-locations>`_
or by passing specific command line options to the ``flake8`` command.

.. important:: The *Flake8* plugin is disabled by default. Add ``docsweeper`` to your
   enabled extensions in your *Flake8* configuration to use it:

   .. code-block:: ini

      [flake8]
      enable-extensions=docsweeper

.. _flake8_file_config:

Plugin Configuration In The Flake8 Configuration File
-----------------------------------------------------

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
----------------------------------------------

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
