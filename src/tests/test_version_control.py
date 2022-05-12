"""Tests for :mod:`_docsweeper.version_control`."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import List, Tuple, Union

import pytest
from faker import Faker
from pytest_cases import fixture, fixture_ref, parametrize, parametrize_with_cases

from _docsweeper.util import RevisionIdentifier
from _docsweeper.version_control import VCSCommandSetConfig, VCSShim, command_sets
from tests.conftest import Repository

faker = Faker()


@fixture
def shim(test_repo: Repository) -> Tuple[Repository, VCSShim]:
    """Return a fixture that combines a test repository and a compatible :class:`VCSShim`.

    :param test_repo: the test repository
    :returns: *test_repo* itself and a compatible shim

    """
    return test_repo, VCSShim(
        test_repo.vcs_command_set_type, test_repo.vcs_command_set_config
    )


class CaseGetFile:
    """Test cases for :func:`.test_get_file_from_repo`."""

    def case_happy(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, List[Tuple[RevisionIdentifier, Path]]]:
        """Success scenario."""
        test_repo = shim[0]
        return (
            test_repo,
            shim[1],
            test_repo.revisions,
        )

    @pytest.mark.xfail(raises=ValueError, strict=True)
    def case_filename_error(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, List[Tuple[RevisionIdentifier, Path]]]:
        """Fail on trying to retrieve a nonexisting file."""
        test_repo = shim[0]
        revisions = copy.deepcopy(test_repo.revisions)
        return (
            test_repo,
            shim[1],
            list(map(lambda x: (x[0], Path("nonexisting_file")), revisions)),
        )

    @parametrize(
        "revision",
        [
            pytest.param(
                "nonexisting_revision",
                marks=pytest.mark.xfail(raises=ValueError, strict=True),
            ),
            pytest.param(
                "",
                marks=pytest.mark.xfail(raises=ValueError, strict=True),
            ),
        ],
    )
    def case_revision_error(
        self, shim: Tuple[Repository, VCSShim], revision: RevisionIdentifier
    ) -> Tuple[Repository, VCSShim, List[Tuple[RevisionIdentifier, Path]]]:
        """Fail upon errors with revision naming."""
        test_repo = shim[0]
        revisions = copy.deepcopy(test_repo.revisions)
        return (test_repo, shim[1], list(map(lambda x: (revision, x[1]), revisions)))


@parametrize_with_cases("repo,shim,revisions", cases=CaseGetFile)
def test_get_file_from_repo(
    repo: Repository, shim: VCSShim, revisions: List[Tuple[RevisionIdentifier, Path]]
) -> None:
    """Test for correct behavior of :meth:`.VCSShim.get_file_from_repo`.

    Uses *shim* to retrieve the file specified in *revisions*. *revisions* is a list of
    tuples, where every tuple consists of a revision identifier, and the path of a file
    in this revision.

    :param repo: a test repository
    :param shim: the shim to be used
    :param revisions: list of revision-file pairs

    """
    for revision, file_ in revisions:
        content = shim.get_file_from_repo(Path(repo.repository_path, file_), revision)
        assert content == repo.helper.get_file(repo.repository_path, revision, file_)


class CaseGetAllRevisions:
    """Test cases for :func:`.test_get_all_revisions`."""

    def case_happy(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, Path]:
        """Happy path."""
        test_repo = shim[0]
        return (test_repo, shim[1], test_repo.revisions[0][1])

    @parametrize(
        "file_name",
        [
            pytest.param(
                "nonexisting_file",
                marks=pytest.mark.xfail(raises=ValueError, strict=True),
            ),
            pytest.param(
                "",
                marks=pytest.mark.xfail(raises=ValueError, strict=True),
            ),
        ],
    )
    def case_filename_error(
        self, shim: Tuple[Repository, VCSShim], file_name: str
    ) -> Tuple[Repository, VCSShim, str]:
        """Fail on errors with the file path."""
        test_repo = shim[0]
        return (test_repo, shim[1], file_name)


@parametrize_with_cases("repo,shim,file_name", cases=CaseGetAllRevisions)
def test_get_all_revisions(
    repo: Repository, shim: VCSShim, file_name: Union[str, Path]
) -> None:
    """Test behavior of :func:`_docsweeper.version_control.VCSShim.get_all_revisions`.

    :param repo: a test repository
    :param shim: the shim to be used
    :param file_name: path of the file for which revisions are retrieved

    """
    file_name = Path(repo.repository_path, file_name)
    revisions = shim.get_all_revisions(file_name)
    expected_revisions = [elem[0] for elem in repo.revisions]
    assert revisions == expected_revisions


class CaseVCSRoot:
    """Test cases for :func:`.test_vcs_root`."""

    def case_happy(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, Path]:
        """Happy path."""
        test_repo = shim[0]
        return test_repo, shim[1], test_repo.revisions[0][1]

    def case_nonexisting(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, str]:
        """Test with nonexisting file."""
        test_repo = shim[0]
        return test_repo, shim[1], "nonexisting_folder/nonexisting_file"

    @parametrize("repo", [fixture_ref("subfolder_repo")])
    def case_subfolder(self, repo: Repository) -> Tuple[Repository, VCSShim, str]:
        """Test on a repository with subfolder."""
        return (
            repo,
            VCSShim(repo.vcs_command_set_type, repo.vcs_command_set_config),
            repo.revisions[0][1].parts[0],
        )

    def case_repository_path(
        self, shim: Tuple[Repository, VCSShim]
    ) -> Tuple[Repository, VCSShim, str]:
        """Test with the repository path itself."""
        return shim[0], shim[1], ""


@parametrize_with_cases("repo,shim,path", cases=CaseVCSRoot)
def test_vcs_root(repo: Repository, shim: VCSShim, path: Union[str, Path]) -> None:
    """Test behavior of :meth:`.VCSShim.vcs_root`.

    :param repo: repository to be used
    :param shim: shim to be used
    :param path: path for which the version control root shall be found

    """
    constructed_path = Path(repo.repository_path, path)
    assert shim.vcs_root(constructed_path) == repo.repository_path


@parametrize(
    "repo", [fixture_ref("moved_file_repo"), fixture_ref("moved_file_subfolder_repo")]
)
def test_get_old_name(repo: Repository) -> None:
    """Test behavior of :meth:`.VCSShim.get_old_name`.

    :param repo: repository to be used

    """

    shim = VCSShim(repo.vcs_command_set_type, repo.vcs_command_set_config)
    old_name = shim.get_old_name(
        Path(repo.repository_path, repo.revisions[0][1]), repo.revisions[1][0]
    )
    assert old_name
    assert Path(old_name) == repo.revisions[2][1]


class VCSCommandSetTestConfigs:
    """Different configurations for use in :func:`test_merge_vcs_command_set_config`."""

    default_config: VCSCommandSetConfig = VCSCommandSetConfig(
        executable=Path("test"), follow_rename=True
    )
    """A default configuration."""
    empty_config: VCSCommandSetConfig = VCSCommandSetConfig()
    """A completely empty configuration."""
    part_config: VCSCommandSetConfig = VCSCommandSetConfig(follow_rename=False)
    """A partly filled configuration."""
    full_config: VCSCommandSetConfig = VCSCommandSetConfig(
        executable=Path("changed"), follow_rename=False
    )
    """A completely customized configuration"""


class CaseTestMerge:
    """Test cases for :func:`test_merge_vcs_command_set_config`."""

    configs = VCSCommandSetTestConfigs

    def case_merge_empty(
        self,
    ) -> Tuple[VCSCommandSetConfig, VCSCommandSetConfig, VCSCommandSetConfig]:
        """Test that merge with empty config returns original config."""
        return (
            self.configs.default_config,
            self.configs.empty_config,
            self.configs.default_config,
        )

    def case_merge_empty_reverse(
        self,
    ) -> Tuple[VCSCommandSetConfig, VCSCommandSetConfig, VCSCommandSetConfig]:
        """Test that merge of empty config with full config returns full config."""
        return (
            self.configs.empty_config,
            self.configs.default_config,
            self.configs.default_config,
        )

    def case_merge_part(
        self,
    ) -> Tuple[VCSCommandSetConfig, VCSCommandSetConfig, VCSCommandSetConfig]:
        """Test merge with partly filled config.

        Values that are set in partly filled config must exist in result.

        # noqa: DAR201

        """
        expected_config = VCSCommandSetConfig(
            executable=self.configs.default_config.executable,
            follow_rename=self.configs.part_config.follow_rename,
        )
        return (self.configs.default_config, self.configs.part_config, expected_config)

    def case_merge_full(
        self,
    ) -> Tuple[VCSCommandSetConfig, VCSCommandSetConfig, VCSCommandSetConfig]:
        """Test merge of full config with another full config.

        Result must be the same as the second config.

        # noqa: DAR201

        """
        return (
            self.configs.default_config,
            self.configs.full_config,
            self.configs.full_config,
        )


@parametrize_with_cases("original, other, expected", cases=CaseTestMerge)
def test_merge_vcs_command_set_config(
    original: VCSCommandSetConfig,
    other: VCSCommandSetConfig,
    expected: VCSCommandSetConfig,
) -> None:
    """Test correct behavior of :func:`VersionControlCommandSet.merge`."""
    result = original.merge(other)

    assert result == expected

    # Verify that original objects are not overwritten:
    assert id(original) != id(result)
    assert id(other) != id(result)


class CaseIsComplete:
    """Test cases for :func:`test_is_complete_vcs_command_set_test_config`."""

    configs = VCSCommandSetTestConfigs

    def case_empty(self) -> Tuple[VCSCommandSetConfig, bool]:
        """Test empty config."""
        return (self.configs.empty_config, False)

    def case_part(self) -> Tuple[VCSCommandSetConfig, bool]:
        """Test partly filled config."""
        return (self.configs.part_config, False)

    def case_full(self) -> Tuple[VCSCommandSetConfig, bool]:
        """Test fully filled config."""
        return (self.configs.full_config, True)


@parametrize_with_cases("config, expected", cases=CaseIsComplete)
def test_is_complete_vcs_command_set_config(
    config: VCSCommandSetConfig, expected: bool
) -> None:
    """Test behavior of :func:`VersionControlCommandSet.is_complete`."""
    assert config.is_complete() == expected
