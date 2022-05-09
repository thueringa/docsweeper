"""Public module of Docsweeper.

This module exports those objects from :mod:`_docsweeper` that are part of the public
API.
"""
from _docsweeper.docsweeper import (
    DocumentedToken,
    DocumentedTokenStatistic,
    analyze_file,
)
from _docsweeper.version_control import (
    GitCommandSet,
    MercurialCommandSet,
    VCSCommandSet,
    VCSCommandSetConfig,
    command_sets,
)

__all__ = [
    "DocumentedToken",
    "DocumentedTokenStatistic",
    "analyze_file",
    "GitCommandSet",
    "MercurialCommandSet",
    "VCSCommandSetConfig",
    "command_sets",
    "VCSCommandSet",
]
