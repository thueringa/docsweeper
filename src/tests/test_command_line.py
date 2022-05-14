"""Unit tests for :mod:`_docsweeper.command_line`.

Test functions that ensure correct handling of command line arguments.

"""
from __future__ import annotations

import argparse
import configparser
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type
from unittest.mock import patch

import click.exceptions
import click.testing
import pytest
from pytest_cases import fixture_ref, parametrize, parametrize_with_cases

import _docsweeper
from _docsweeper.command_line import parse_args
from _docsweeper.version_control import VCSCommandSet, VCSCommandSetConfig, command_sets
from tests.conftest import _VCSHelper


class CasesArguments:
    """Test cases for :func:`.test_argparser`."""

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_default(
        self,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that default parameters are set."""

        default_command_set, default_config = command_sets["git"]
        return ["hello"], {
            "files": [Path("hello")],
            "vcs_command_set_type": default_command_set,
            "vcs_command_set_config": default_config,
        }

    @parametrize("config", [fixture_ref("command_set_test_config")])
    @parametrize("option", ["--debug", "-d", "--verbose", "-v"])
    def case_single_option(
        self,
        option: str,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test options."""

        default_command_set, default_config = command_sets["git"]
        return [option, "hello"], {
            "files": [Path("hello")],
            "vcs_command_set_type": default_command_set,
            "vcs_command_set_config": default_config,
        }

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_no_follow(
        self,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that ``--no-follow-rename`` option is handled correctly."""
        _, default_config = command_sets["git"]
        expected_config = default_config.merge(VCSCommandSetConfig(follow_rename=False))
        return ["--no-follow-rename", "hello"], {
            "vcs_command_set_config": expected_config
        }

    def case_combined_short(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that combined options are handled correctly."""
        return ["-vd", "hello"], {
            "files": [Path("hello")],
        }

    def case_multiple_files(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that passing multiple files is handled correctly."""
        return (
            ["hello", "other/file"],
            {
                "files": [Path("hello"), Path("other/file")],
            },
        )

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_consume_strings(
        self,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that parameters that consume strings are handle correctly."""
        return (
            ["--vcs", "git", "other/file"],
            {
                "files": [Path("other/file")],
                "vcs_command_set_type": git_config[0],
            },
        )

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_vcs(
        self,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that vcs option is handled correctly."""
        return ["--vcs", str(config[0].name), "other/file"], {
            "vcs_command_set_type": config[0],
        }

    @pytest.mark.xfail(raises=click.exceptions.BadParameter, strict=True)
    def case_vcs_unsupported(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that passing unsupported vcs is handled correctly."""
        return ["--vcs", "cat", "other/file"], {}

    @pytest.mark.xfail(raises=click.exceptions.BadOptionUsage, strict=True)
    def case_vcs_missing(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that missing vcs option is handled correctly."""
        return ["--vcs"], {}

    @pytest.mark.xfail(strict=True)
    def case_missing_file(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that missing files are handled correctly."""
        return ["--debug"], {}

    def case_vcs_executable(
        self,
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that passing option ``--vcs-executable`` is handled correctly."""
        location = "someplace"
        expected_config = git_config[1].merge(
            VCSCommandSetConfig(executable=Path(location))
        )
        return (
            ["--vcs-executable", location, "hello"],
            {
                "files": [Path("hello")],
                "vcs_command_set_config": expected_config,
            },
        )

    @pytest.mark.skip(reason="See issue0005")
    @pytest.mark.xfail(raises=argparse.ArgumentError, strict=True)
    def case_no_arguments(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that passing no arguments at all is handled correctly."""
        return [], {}

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_config(
        self,
        tmp_path: Path,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that passing the ``--config`` option is handled correctly."""
        customization = VCSCommandSetConfig(executable=Path("gat"))
        config_path = Path(tmp_path, "config.ini")
        ini_config = configparser.ConfigParser()
        ini_config.read_dict(
            {
                "docsweeper": {"follow_rename": False, "vcs": str(config[0].name)},
                f"docsweeper.{str(config[0].name)}": {"executable": "gat"},
            }
        )
        with open(config_path, "w") as config_file_:
            ini_config.write(config_file_)
        expected_config = (
            config[1]
            .merge(customization)
            .merge(VCSCommandSetConfig(follow_rename=False))
        )
        return (
            ["-c", str(config_path), "file"],
            {"vcs_command_set_config": expected_config},
        )

    @parametrize("config", [fixture_ref("command_set_test_config")])
    def case_config_change_shim(
        self,
        tmp_path: Path,
        config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that ``vcs`` ini-config option is handled correctly."""
        config_path = Path(tmp_path, "config.ini")
        ini_config = configparser.ConfigParser()
        ini_config.read_dict({"docsweeper": {"vcs": str(config[0].name)}})
        with open(config_path, "w") as config_file_:
            ini_config.write(config_file_)
        return (
            ["-c", str(config_path), "file"],
            {"vcs_command_set_type": config[0]},
        )

    @pytest.mark.xfail(strict=True)
    def case_config_unreadable(self) -> Tuple[List[str], Dict[str, Any]]:
        """Test that nonexisting config is handled correctly."""
        return (["-c", str("nonexisting"), "file"], {})

    @pytest.mark.xfail(strict=True)
    def case_config_unsupported(
        self,
        tmp_path: Path,
        git_config: Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]],
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Test that using unsupported config option is handled correctly."""
        customization = {"exacutable": Path("gat")}
        config_path = Path(tmp_path, "config.ini")
        config = configparser.ConfigParser()
        config.read_dict({"docsweeper.git": customization})
        with open(config_path, "w") as config_file_:
            config.write(config_file_)
        return (["-c", str(config_path), "file"], {})


@parametrize_with_cases("arguments, expected", cases=CasesArguments)
def test_argparser(arguments: List[str], expected: Dict[str, Any]) -> None:
    """Test for correct argument parsing."""
    with patch("tests.test_command_line.parse_args._result_callback") as mocked_run:
        parse_args.main(arguments, standalone_mode=False)
        parsed = mocked_run.call_args[0][0]
        mocked_run.assert_called()
        for arg_name in expected.keys():
            assert arg_name in parsed
            assert parsed[arg_name] == expected[arg_name]


class CasesVerbosity:
    """Test cases for :func:`.test_handle_verbosity_args`."""

    @parametrize(
        "arguments, expected",
        [
            (["--verbose", "file"], logging.INFO),
            (["--debug", "file"], logging.DEBUG),
            (["-v", "file"], logging.INFO),
            (["-d", "file"], logging.DEBUG),
        ],
        idgen="{arguments}",
    )
    def case_verbosity(
        self, arguments: List[str], expected: int
    ) -> Tuple[List[str], int]:
        """Test that verbosity options change logger level correctly."""
        return arguments, expected


@parametrize_with_cases("arguments,expected", cases=CasesVerbosity)
def test_handle_verbosity_args(arguments: List[str], expected: int) -> None:
    """Test that verbosity arguments are handled correctly."""
    with patch("tests.test_command_line.parse_args._result_callback"):
        parse_args.main(arguments, standalone_mode=False)
        assert _docsweeper.logger.level == expected


def test_help_epilog() -> None:
    """Test that help prints epilog and contains all wanted information.

    For every available command set, its name and default executable location must be
    printed in the help epilog.

    """
    ctx = click.Context(parse_args)
    help_text = parse_args.get_help(ctx)
    for command_set, config in command_sets.values():
        assert command_set.name in help_text
        assert str(config.executable) in help_text
