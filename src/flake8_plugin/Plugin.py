"""The Flake8 module parts of Docsweeper."""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any, Generator, Tuple, Type

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

import docsweeper


class Plugin:
    """Run docsweeper as a flake8 plugin."""

    name = "docsweeper"
    version = version("docsweeper")
    err_value = "DOC100"
    _max_changes: int
    """Maximum allowed changes of code since last docstring change before DOC100 triggers.

    Users can change this via command line parameter and configuration file.

    """
    _follow_rename: bool
    """Follow version control history along renames of files.

    Users can change this via command line parameter and configuration file.

    """
    _vcs_type: Type[docsweeper.VCSCommandSet]
    """The version control system that is used.

    Users can change this via command line parameter and configuration file.

    """
    _vcs_executable: str
    """Path of the version control system executable.

    Users can change this via command line parameter and configuration file.

    """

    def __init__(self, tree: ast.Module, filename: str, options: argparse.Namespace):
        """Analyze *filename*."""
        self.filename = filename
        self.tree = tree
        self._parse_options(options)
        self.off_by_default = True

        self._token_statistics = []
        if (
            Plugin.name not in options.enable_extensions
            and Plugin.err_value not in options.enable_extensions
        ):
            return
        default_config = docsweeper.command_sets[self._vcs_type.name][1]
        executable = (
            Path(self._vcs_executable)
            if self._vcs_executable
            else default_config.executable
        )
        follow_rename = (
            self._follow_rename if self._follow_rename else default_config.follow_rename
        )
        command_set_config = docsweeper.VCSCommandSetConfig(
            executable=executable, follow_rename=follow_rename
        )
        self._token_statistics = docsweeper.analyze_file(
            self._vcs_type, command_set_config, Path(filename).resolve()
        )

    def run(self) -> Generator[Tuple[int, int, str, Any], None, None]:
        """Perform reporting step."""
        for token, statistic in self._token_statistics:
            if statistic.code_changes > self._max_changes:
                yield (
                    token.lineno,
                    0,
                    (
                        f"{Plugin.err_value} Potentially outdated docstring: "
                        f"{statistic.code_changes} code "
                        f"change{'s' if statistic.code_changes > 1 else ''} in "
                        f"{token.name} since last docstring change"
                    ),
                    None,
                )

    def add_options(option_manager):  # type: ignore
        """Add our custom options to the flake8 options parser."""
        option_manager.add_option(  # type:ignore
            "--max-changes",
            type=int,
            default=0,
            parse_from_config=True,
            help=(
                "Maximum allowed changes of code since last docstring change before "
                f"{Plugin.err_value} triggers. "
            ),
        )
        option_manager.add_option(  # type:ignore
            "--no-follow-rename",
            type=bool,
            parse_from_config=True,
            help="Follow version control history along renames of files.",
        )
        option_manager.add_option(  # type:ignore
            "--vcs",
            type=str,
            choices=[
                command_set.name for command_set, _ in docsweeper.command_sets.values()
            ],
            default=iter(docsweeper.command_sets.values()).__next__()[0].name,
            parse_from_config=True,
            help="Choose the type of version control system.",
        )
        option_manager.add_option(  # type:ignore
            "--vcs-executable",
            type=str,
            parse_from_config=True,
            help="Path of the executable of the version control system.",
        )

    def _parse_options(self, options: argparse.Namespace) -> None:
        """Populate class attributes with parsed option objects."""
        self._max_changes = options.max_changes
        self._follow_rename = not options.no_follow_rename
        self._vcs_type = (
            command_set
            for command_set, _ in docsweeper.command_sets.values()
            if command_set.name == options.vcs
        ).__next__()
        self._vcs_executable = (
            options.vcs_executable if options.vcs_executable else None
        )
