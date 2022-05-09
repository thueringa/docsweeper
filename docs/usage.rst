Usage
=====

*Docsweeper* can be used as a *Flake8* plugin, from the command line, or directly from
*Python* code.

.. _usage_plugin:

Using Docsweeper As A Flake8 plugin
-----------------------------------

Upon installation, *Docsweeper* will register itself automatically as a plugin for
*Flake8* if it is installed. See :ref:`configuration instructions <flake8_config>` for
instructions on how to configure the plugin.

Error/Violation Codes
---------------------

*Docsweeper* employs the following *Flake8* error codes:

.. _DOC100:

DOC100 Potentially Outdated Docstring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code of this token has changed more times than allowed since the docstring that
references it has been updated.

The amount of allowed code changes until this violation triggers is determined by the
``--max_changes`` :ref:`command line option <max_changes>` or ``max_changes``
option in the :ref:`Flake8 configuration file <flake8_file_config>`.

.. _usage_cmdline:

Invoking Docsweeper From Command Line
-------------------------------------

A list of available version control system interfaces and their default
executable locations is printed at the end of the command line help:

.. code-block:: console

   $ docsweeper -h

For example, to analyze the source file :file:`source.py` in a git repository, run:

.. code-block:: console

   $ docsweeper --vcs-shim git source.py

If the default executable location for your version control system is not correct for
your system, override it using :code:`--vcs-executable` option or a :ref:`configuration
file <file_config>`:

.. code-block:: console

   $ docsweeper --vcs-shim git --vcs-executable /path/to/git source.py

Invoking Docsweeper From Python Code
------------------------------------

See :ref:`code-usage`.
