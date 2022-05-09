==================================
 :mod:`docsweeper` --- Public API
==================================

In this part we describe the public python API of Docsweeper, and show how to use it in
code.

.. _code-usage:

Example Usage
=============

The following code snippet shows how Docsweeper can be employed in code:

.. code-block:: python

   import docsweeper
   from pathlib import Path

   file_ = Path("code.py")

   # create configuration object:
   config = VCSCommandSetConfig(
       executable="/usr/bin/git",
       follow_rename=True
   )

   # choose version control system:
   vcs = docsweeper.GitCommandSet

   # run analysis and obtain results:
   results = docsweeper.analyze(vcs, config, file_)

Running :func:`docsweeper.analyze_file` will parse and analyze the input file. See the
full API below for more information on the data types used for the results.

API
===

.. py:module:: docsweeper

This is the public Python API of Docsweeper.

Client Entry Points
-------------------

Use :func:`docsweeper.analyze_file` to retrieve statistics about the docstrings of all
the tokens in a file:

.. autofunction:: docsweeper.analyze_file

   .. versionadded:: 0.3.0

Result Data Types
-----------------

These are the types used in the return value of :func:`docsweeper.analyze_file`:

.. autoclass:: docsweeper.DocumentedToken
   :members:
   :exclude-members: __new__,__init__
   :show-inheritance:

.. autoclass:: docsweeper.DocumentedTokenStatistic
   :members:
   :exclude-members: __new__,__init__
   :show-inheritance:

Version Control
---------------

These classes are concerned with the interaction with the Version control system, and
are passed as parameters to :func:`docsweeper.analyze_file`.
:class:`docsweeper.GitCommandSet` and :class:`docsweeper.MercurialCommandSet` define the
kind of version control system used, while :class:`docsweeper.VCSCommandSetConfig`
provides user-defined parameters to customize version control behavior.

.. autoclass:: docsweeper.VCSCommandSet
   :members:
   :exclude-members: __new__, __init__
   :show-inheritance:

   .. versionadded:: 0.4.0
.. autoclass:: docsweeper.GitCommandSet
   :members:
   :exclude-members: __init__
   :show-inheritance:

.. autoclass:: docsweeper.MercurialCommandSet
   :members:
   :exclude-members: __init__
   :show-inheritance:

.. autoclass:: docsweeper.VCSCommandSetConfig
   :members:
   :exclude-members: __new__,__init__
   :show-inheritance:

.. autoattribute:: docsweeper::command_sets

   Dictionary of all supported command sets and their default configuration.

   .. versionadded:: 0.3.0
