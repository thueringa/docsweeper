"""Tests for :mod:`_docsweeper.docsweeper`."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Type

import pytest
from faker import Faker
from pytest_cases import fixture_ref, parametrize, parametrize_with_cases

from _docsweeper.docsweeper import (
    ParserError,
    _DocumentedTokenVisitor,
    _get_documented_tokens,
    analyze_file,
)
from _docsweeper.version_control import (
    VCSCommandSet,
    VCSCommandSetConfig,
    VCSExecutableError,
)
from tests.conftest import Repository


class CasesTokenHistory:
    """Test cases for :func:`test_documented_token_history`."""

    @parametrize(
        "repo,config,expected",
        [
            (
                fixture_ref(repo),
                VCSCommandSetConfig(follow_rename=True),
                (1, 2, 1),
            )
            for repo in ["simple_repo", "subfolder_repo"]
        ]
        + [
            (
                fixture_ref(repo),
                VCSCommandSetConfig(follow_rename=False),
                (1, 2, 1),
            )
            for repo in ["simple_repo", "subfolder_repo"]
        ]
        + [
            (
                fixture_ref(repo),
                VCSCommandSetConfig(follow_rename=True),
                (1, 4, 2),
            )
            for repo in ["moved_file_repo", "moved_file_subfolder_repo"]
        ]
        + [
            (  # type: ignore
                fixture_ref(repo),
                VCSCommandSetConfig(follow_rename=False),
                (1, None, 1),
            )
            for repo in ["moved_file_repo", "moved_file_subfolder_repo"]
        ],
        idgen="{repo}-{config}",
    )
    def case_repo(
        self,
        repo: Repository,
        config: VCSCommandSetConfig,
        expected: Tuple[int, Optional[int], int],
    ) -> Tuple[Repository, VCSCommandSetConfig, Tuple[int, Optional[int], int]]:
        """Return a repo, a compatible config, and the expected analysis results."""
        extended_config = repo.vcs_command_set_config.merge(config)
        return repo, extended_config, expected


@parametrize_with_cases("repo,config,expected", cases=CasesTokenHistory)
def test_documented_token_history(
    repo: Repository,
    config: VCSCommandSetConfig,
    expected: Tuple[int, Optional[int], int],
) -> None:
    """Test correctness of token history returned by :func:`.analyze_file`."""
    history = analyze_file(
        repo.vcs_command_set_type,
        config,
        repo.repository_path.joinpath(repo.revisions[0][1]),
    )
    assert len(history) == expected[0]
    token_history = history[0][1]
    if expected[1]:
        assert token_history.last_docstring_change
        assert token_history.last_docstring_change[1] == expected[1]
    else:
        assert token_history.last_docstring_change is None
    assert token_history.code_changes == expected[2]


def test_fully_qualified_names(
    tmpdir_factory: pytest.TempdirFactory, faker: Faker
) -> None:
    """Test correct creation of fully qualified names."""
    repository_path = Path(tmpdir_factory.mktemp("nametest"))
    code_file = repository_path.joinpath("mymodule.py")
    code_file.write_text(
        "\n".join(
            [
                '"""Test module"""',
                "class Test:",
                '    """docstring"""',
                "    def test_fun(self):",
                '        """docs"""',
                "        pass",
            ]
        )
    )
    documented_tokens = _get_documented_tokens(code_file)
    for name in [code_file.stem, "Test", "Test.test_fun"]:
        assert name in documented_tokens.keys()


def test_repo_path_is_not_repository(
    tmpdir_factory: pytest.TempdirFactory, simple_repo: Repository
) -> None:
    """Test that :class:`.VCSShim` can not be instantiated with an invalid repository path.

    :param simple_repo: the repository
    :param tmpdir_factory: for creating the repo dir
    """
    repository_path = str(tmpdir_factory.mktemp("repository"))
    code_file = Path(repository_path).joinpath("mymodule.py")
    code_file.write_text(
        """\"\"\"Test module\"\"\"
def test_fun():
    \"\"\"docs\"\"\"
    pass"""
    )
    with pytest.raises(ValueError, match="does not seem to be under version control"):
        analyze_file(
            simple_repo.vcs_command_set_type,
            simple_repo.vcs_command_set_config.merge(
                VCSCommandSetConfig(follow_rename=True)
            ),
            code_file,
        )


def test_token_visitor_generates_correct_token_attributes(
    tmpdir_factory: pytest.TempdirFactory,
) -> None:
    """Test that attributes of documented tokens are filled correctly when parsed."""

    # create code file with test code:
    root = str(
        tmpdir_factory.mktemp(
            test_token_visitor_generates_correct_token_attributes.__name__
        )
    )
    mod_name = "test"
    code_file = Path(root).joinpath(f"{mod_name}.py")
    fn_name = "test_fun"
    elements = {mod_name: {"docstring": "Test module"}, fn_name: {"docstring": "docs"}}
    code_file.write_text(
        (
            f'"""{elements[mod_name]["docstring"]}"""\n'
            f"def {fn_name}():\n"
            f'    """{elements[fn_name]["docstring"]}"""\n'
            "    pass\n"
        )
    )

    # parse file and check for correct attributes in result.
    visitor = _DocumentedTokenVisitor(code_file)
    for element_name, element in elements.items():
        assert element_name in visitor.documented_tokens
        assert visitor.documented_tokens[element_name].docstring == element["docstring"]


class _CasesTestAnalyzeFilePathErrors:
    @pytest.mark.xfail(raises=FileNotFoundError, strict=True)
    def case_nonexisting_file(
        self, test_repo: Repository
    ) -> Tuple[Path, Type[VCSCommandSet], VCSCommandSetConfig]:
        return (
            Path("nonexisting_file"),
            test_repo.vcs_command_set_type,
            test_repo.vcs_command_set_config,
        )

    @pytest.mark.xfail(raises=ParserError, strict=True)
    def case_invalid_python_file(
        self, test_repo: Repository, tmpdir_factory: pytest.TempdirFactory
    ) -> Tuple[Path, Type[VCSCommandSet], VCSCommandSetConfig]:
        root = tmpdir_factory.mktemp("temp")
        file_ = Path(root, "invalid.py")
        with open(file_, "w") as writer:
            writer.write("definitely not(python:2='}")
        return (
            file_,
            test_repo.vcs_command_set_type,
            test_repo.vcs_command_set_config,
        )

    @pytest.mark.xfail(raises=VCSExecutableError, strict=True)
    def case_nonexisting_executable(
        self, test_repo: Repository
    ) -> Tuple[Path, Type[VCSCommandSet], VCSCommandSetConfig]:
        changed_config = test_repo.vcs_command_set_config.merge(
            VCSCommandSetConfig(executable=Path("nonexisting"))
        )
        return (
            Path(test_repo.repository_path, test_repo.revisions[0][1]),
            test_repo.vcs_command_set_type,
            changed_config,
        )

    @pytest.mark.xfail(raises=VCSExecutableError, strict=True)
    def case_nonexecutable_executable(
        self, test_repo: Repository, tmpdir_factory: pytest.TempdirFactory
    ) -> Tuple[Path, Type[VCSCommandSet], VCSCommandSetConfig]:
        root = tmpdir_factory.mktemp("temp")
        file_ = Path(root, "nonexecutable")
        file_.touch()
        changed_config = test_repo.vcs_command_set_config.merge(
            VCSCommandSetConfig(executable=file_)
        )
        return (
            Path(test_repo.repository_path, test_repo.revisions[0][1]),
            test_repo.vcs_command_set_type,
            changed_config,
        )


@parametrize_with_cases(
    "path,vcs_type,vcs_config", cases=_CasesTestAnalyzeFilePathErrors
)
def test_analyze_file_errors(
    path: Path, vcs_type: Type[VCSCommandSet], vcs_config: VCSCommandSetConfig
) -> None:
    """Test :func:`docsniffer.analyze_file` with wrong files and executables."""
    analyze_file(
        vcs_type, vcs_config.merge(VCSCommandSetConfig(follow_rename=True)), path
    )
