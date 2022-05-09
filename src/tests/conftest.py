"""Main test configuration and fixtures.

Provides the fixtures :func:`.simple_repo`, :func:`.moved_file_repo`. These fixtures
offer readymade repositories and corresponding helper classes via the
:class:`.Repository` instance variable. There is a fixture ``vcs_test_config`` that
provides all avaible repositories in succession to a single test function.

"""
from __future__ import annotations

import configparser
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Type

import pytest
from faker import Faker
from pytest_cases import fixture, fixture_union

from _docsweeper.util import RevisionIdentifier, call_subprocess
from _docsweeper.version_control import (
    GitCommandSet,
    MercurialCommandSet,
    VCSCommandSet,
    VCSCommandSetConfig,
    VCSShim,
)


class _VCSHelper(ABC):
    """Some convenience functions around the version control system during tests."""

    def __init__(self, executable: Path):
        """Create a new instance of this helper.

        :param executable: path of the executable for this helper.

        """
        self.executable: Path = executable

    @abstractmethod
    def get_revisions(self, repository_path: Path, file_name: Path) -> List[str]:
        """Return a list of all revisions for *file_name* in *repository_path*.

        :param repository_path: A valid git repository
        :param file_name: path of the file
        :return: A string containing the identifier of the revision
        :raises subprocess.SubprocessError: if the underlying command fails
        """

        pass

    @abstractmethod
    def add_file(self, code_file: Path, repository_path: Path) -> None:
        """Add *code_file* to the git repository in *repository_path*.

        :param code_file: path of the file relative to *repository_path*
        :param repository_path: path of the base repository
        :raises subprocess.SubprocessError: if the underlying command fails
        """
        pass

    @abstractmethod
    def get_file(
        self,
        repository_path: Path,
        revision: RevisionIdentifier,
        file_name: Path,
    ) -> str:
        """Return the the contents of *file_name* in *revision*.

        :param repository_path: A valid git repository
        :param revision: a revision identifier
        :param file_name: path of the file
        :return: the files' contents
        :raises subprocess.SubprocessError: if the underlying command fails

        """
        pass

    @abstractmethod
    def move_file(
        self,
        repository_path: Path,
        file_from: Path,
        file_to: Path,
    ) -> None:
        """Move file *file_from* to destination *file_to*.

        :param repository_path: the repository path
        :param file_from: origin file
        :param file_to: destination

        """
        pass

    @abstractmethod
    def commit(self, message: str, repository_path: Path) -> None:
        """Commit the changes made to the version control system.

        :param message: the commit message
        :param repository_path: the repository path

        """
        pass

    def write_and_commit_content(
        self,
        file_: Path,
        content: str,
        commit_message: str,
        repository_path: Path,
    ) -> None:
        """Write *content* to *file_* and commit to the version control system.

        :param file_: path of the file to be written
        :param content: content that shall be written into *file_*
        :param commit_message: a commit message
        :param repository_path: the repository path

        """
        file_.parent.mkdir(parents=True, exist_ok=True)
        file_.write_text(content, "utf-8")
        self.add_file(file_, repository_path)
        self.commit(commit_message, repository_path)


class Repository(NamedTuple):
    """Provides everything needed to test a command set on a real repository.

    Holds an instance of :class:`~.VCSShim` in *shim*. To enable comfortable
    inspection of the repository during tests, a list of revision names is found in
    *revisions*, as well as the path of a file *code_file*, which is checked into the
    version control system. *repository_path* holds the path of the repository itself.

    """

    repository_path: Path
    """Path of the repository in the file system."""
    revisions: List[Tuple[str, Path]]
    """List of revision lists and test files.

    A list of tuples, each consisting of a revision identifier, and the name of a file
    in this revision.

    """
    shim: VCSShim
    helper: _VCSHelper
    vcs_command_set_type: Type[VCSCommandSet]
    vcs_command_set_config: VCSCommandSetConfig


@fixture(scope="session")
def user_config(
    pytestconfig: pytest.Config,
) -> configparser.ConfigParser:
    """Read pytest.ini again to retrieve extra values provided by the user."""
    ini_path = pytestconfig.inipath
    config = configparser.ConfigParser()
    if ini_path:
        config.read(ini_path)
    return config


CommandSetTestConfig = Tuple[Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]]


@fixture(scope="session")
def git_config(
    user_config: configparser.ConfigParser,
) -> CommandSetTestConfig:
    """Encapsulate a complete command set, config, and helper for git in a fixture."""
    return _create_command_set_test_config(
        user_config, GitCommandSet, _GitHelper, "git_executable"
    )


def _create_command_set_test_config(
    user_config: configparser.ConfigParser,
    command_set: Type[VCSCommandSet],
    helper: Type[_VCSHelper],
    executable_option: str,
    pytest_option_name: Optional[str] = None,
) -> CommandSetTestConfig:
    """Create a command set test config ready for use by tests.

    :param user_config: user configuration object
    :param helper: type of helper that is to be used
    :param command_set: type of version control command set that is to be used
    :param executable_option: name of the option in *user_config* that defines the
        location of the vcs executable"
    :param pytest_option_name: name of the pytest option that discards tests using
        this config from the test run. Used for the help string, and ignored if
        ``None``.
    :returns: the test configuration
    """
    executable = _get_executable_from_config(
        user_config, "docsweeper", executable_option, pytest_option_name
    )
    return (
        command_set,
        VCSCommandSetConfig(
            executable=Path(executable),
            follow_rename=True,
        ),
        helper,
    )


def _get_executable_from_config(
    user_config: configparser.ConfigParser,
    section: str,
    option: str,
    pytest_option_name: Optional[str] = None,
) -> str:
    user_executable = user_config.get(section, option)
    if not user_executable:
        print(
            (
                f"No value set in pytest.ini for '{section}.{option}'! ",
                f"Either set one or run the tests with option '--{pytest_option_name}'."
                if pytest_option_name
                else "Please set one.",
            ),
            file=sys.stderr,
        )
        sys.exit(2)
    if not os.access(user_executable, os.X_OK):
        print(
            (
                f"{user_executable} set for '{section}.{option} in pytest.ini is not "
                "executable."
            ),
            file=sys.stderr,
        )
        sys.exit(2)
    return user_executable


@fixture(scope="session")
def old_git_config(
    user_config: configparser.ConfigParser, pytestconfig: pytest.Config
) -> Optional[CommandSetTestConfig]:
    """Encapsulate a complete command set, config, and helper for an old git version."""
    if pytestconfig.option.no_old_git:
        return None
    return _create_command_set_test_config(
        user_config,
        GitCommandSet,
        _GitHelper,
        "old_git_executable",
        "no_old_git",
    )


@fixture(scope="session")
def old_hg_config(
    user_config: configparser.ConfigParser, pytestconfig: pytest.Config
) -> Optional[CommandSetTestConfig]:
    """Encapsulate a complete command set, config, and helper for an old hg version."""
    if pytestconfig.option.no_old_hg:
        return None
    return _create_command_set_test_config(
        user_config,
        MercurialCommandSet,
        _MercurialHelper,
        "old_hg_executable",
        "no_old_hg",
    )


@fixture(scope="session")
def hg_config(
    user_config: configparser.ConfigParser,
) -> CommandSetTestConfig:
    """Encapsulate a complete command set, config, and helper for mercurial."""
    return _create_command_set_test_config(
        user_config,
        MercurialCommandSet,
        _MercurialHelper,
        "hg_executable",
    )


command_set_test_config = fixture_union(
    "command_set_test_config",
    [git_config, hg_config, old_git_config, old_hg_config],
    scope="session",
)
"""Fixture union for all test configs that are to be used."""


class _GitHelper(_VCSHelper):
    """An instance of :class:`_VCSHelper` for git."""

    def get_revisions(self, repository_path: Path, file_name: Path) -> List[str]:
        result = call_subprocess(
            [
                str(self.executable),
                "--no-pager",
                "log",
                "--follow",
                "--format=%H",
                str(file_name),
            ],
            cwd=repository_path,
        )
        return result.splitlines()

    def add_file(self, code_file: Path, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "add", str(code_file)],
            cwd=repository_path,
        )

    def get_file(
        self,
        repository_path: Path,
        revision: RevisionIdentifier,
        file_name: Path,
    ) -> str:
        return call_subprocess(
            [
                str(self.executable),
                "--no-pager",
                "show",
                f"{revision}:{str(file_name)}",
            ],
            cwd=repository_path,
        ).rstrip()

    def move_file(
        self,
        repository_path: Path,
        file_from: Path,
        file_to: Path,
    ) -> None:
        call_subprocess(
            [str(self.executable), "mv", f"{str(file_from)}", f"{str(file_to)}"],
            cwd=repository_path,
        )

    def commit(self, message: str, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "commit", "-m", message],
            cwd=repository_path,
        )


class _MercurialHelper(_VCSHelper):
    """An instance of :class:`_VCSHelper` for mercurial."""

    def get_revisions(self, repository_path: Path, file_name: Path) -> List[str]:
        result = call_subprocess(
            [
                str(self.executable),
                "--pager=never",
                "log",
                "-f",
                "--template={node}\n",
                str(file_name),
            ],
            cwd=repository_path,
        )
        return result.splitlines()

    def add_file(self, code_file: Path, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "add", str(code_file)],
            cwd=repository_path,
        )

    def get_file(
        self,
        repository_path: Path,
        revision: RevisionIdentifier,
        file_name: Path,
    ) -> str:
        return call_subprocess(
            [
                str(self.executable),
                "--pager=never",
                "cat",
                "-r",
                revision,
                str(file_name),
            ],
            cwd=repository_path,
        ).rstrip()

    def move_file(
        self,
        repository_path: Path,
        file_from: Path,
        file_to: Path,
    ) -> None:
        call_subprocess(
            [str(self.executable), "mv", str(file_from), str(file_to)],
            cwd=repository_path,
        )

    def commit(self, message: str, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "commit", "-m", message],
            cwd=repository_path,
        )


@fixture(scope="session")
def simple_repo(
    command_set_test_config: Tuple[
        Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]
    ],
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
) -> Repository:
    """Return simple repository fixture containing only a single file."""
    command_set, vcs_config, vcs_helper = command_set_test_config
    assert vcs_config.executable is not None
    return _build_simple_repo(
        tmpdir_factory,
        command_set,
        vcs_config,
        vcs_helper(vcs_config.executable),
        f"simple_{command_set.name}_repo",
        faker.file_name(),
    )


@fixture(scope="session")
def subfolder_repo(
    command_set_test_config: Tuple[
        Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]
    ],
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
) -> Repository:
    """Return a repository fixture containing a file in a subfolder."""
    command_set, vcs_config, vcs_helper = command_set_test_config
    assert vcs_config.executable is not None
    return _build_simple_repo(
        tmpdir_factory,
        command_set,
        vcs_config,
        vcs_helper(vcs_config.executable),
        f"simple_{command_set.name}_repo",
        Path("subfolder", faker.file_name()),
    )


@fixture(scope="session")
def moved_file_subfolder_repo(
    command_set_test_config: Tuple[
        Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]
    ],
    faker: Faker,
    tmpdir_factory: pytest.TempdirFactory,
) -> Repository:
    """Return a repository fixture that contains in a subfolder that has been moved."""
    command_set, vcs_config, vcs_helper_type = command_set_test_config
    assert vcs_config.executable is not None
    vcs_helper = vcs_helper_type(vcs_config.executable)
    test_repo = _build_simple_repo(
        tmpdir_factory,
        command_set,
        vcs_config,
        vcs_helper,
        f"moved_{command_set.name}_repo",
        Path("subfolder", faker.file_name()),
    )
    repository_path = test_repo.repository_path
    code_file = test_repo.revisions[0][1]
    destination_file = repository_path.joinpath("subfolder", faker.file_name())
    vcs_helper.move_file(repository_path, code_file, destination_file)
    vcs_helper.commit("moved file.", repository_path)

    new_content = """def test_function():
    \"\"\"test a function\"\"\"
    return 6"""
    vcs_helper.write_and_commit_content(
        destination_file, new_content, "Changed code.", repository_path
    )
    revisions = test_repo.revisions
    new_revisions = vcs_helper.get_revisions(repository_path, destination_file)[:2]
    new_revisions.reverse()
    for revision in new_revisions:
        revisions.insert(
            0,
            (
                revision,
                destination_file.relative_to(repository_path),
            ),
        )

    return Repository(
        repository_path,
        revisions,
        test_repo.shim,
        test_repo.helper,
        test_repo.vcs_command_set_type,
        test_repo.vcs_command_set_config,
    )


@pytest.fixture(scope="session")
def faker() -> Faker:
    """Return a session-scoped faker instance.

    The default faker fixture is function-scoped and can not be used
    in higher-scoped fixtures.

    :returns: the faker fixture
    """
    return Faker()


@fixture(scope="session")
def moved_file_repo(
    command_set_test_config: Tuple[
        Type[VCSCommandSet], VCSCommandSetConfig, Type[_VCSHelper]
    ],
    faker: Faker,
    tmpdir_factory: pytest.TempdirFactory,
) -> Repository:
    """Return a repository fixture  with a file that has been moved at some point."""
    command_set, vcs_config, vcs_helper_type = command_set_test_config
    assert vcs_config.executable is not None
    vcs_helper = vcs_helper_type(vcs_config.executable)
    test_repo = _build_simple_repo(
        tmpdir_factory,
        command_set,
        vcs_config,
        vcs_helper,
        f"moved_{command_set.name}_repo",
        faker.file_name(),
    )
    repository_path = test_repo.repository_path
    code_file = test_repo.revisions[0][1]
    destination_file = repository_path.joinpath(faker.file_name())
    vcs_helper.move_file(repository_path, code_file, destination_file)
    vcs_helper.commit("moved file.", repository_path)

    new_content = """def test_function():
    \"\"\"test a function\"\"\"
    return 6"""
    vcs_helper.write_and_commit_content(
        destination_file, new_content, "Changed code.", repository_path
    )
    revisions = test_repo.revisions
    new_revisions = vcs_helper.get_revisions(repository_path, destination_file)[:2]
    new_revisions.reverse()
    for revision in new_revisions:
        revisions.insert(
            0,
            (
                revision,
                destination_file.relative_to(repository_path),
            ),
        )

    return Repository(
        repository_path,
        revisions,
        test_repo.shim,
        test_repo.helper,
        test_repo.vcs_command_set_type,
        test_repo.vcs_command_set_config,
    )


def _build_simple_repo(
    tmpdir_factory: pytest.TempdirFactory,
    command_set: Type[VCSCommandSet],
    command_set_config: VCSCommandSetConfig,
    vcs_helper: _VCSHelper,
    repository_name: str,
    file_name: Path,
) -> Repository:
    """Create a test repository from parameters."""
    repository_path = Path(tmpdir_factory.mktemp(repository_name))
    call_subprocess([str(command_set_config.executable), "init", str(repository_path)])
    revisions = []

    code_file = repository_path.joinpath(file_name)
    for index, content in enumerate(
        [
            """def test_function():
    \"\"\"test function\"\"\"
    return 3""",
            """def test_function():
    \"\"\"test a function\"\"\"
    return 3""",
            """def test_function():
    \"\"\"test a function\"\"\"
    return 2""",
        ]
    ):
        vcs_helper.write_and_commit_content(
            code_file, content, f"commit #{index}", repository_path
        )
    revisions = [
        (revision, code_file.relative_to(repository_path))
        for revision in vcs_helper.get_revisions(repository_path, code_file)
    ]
    return Repository(
        repository_path,
        revisions,
        VCSShim(command_set, command_set_config),
        vcs_helper,
        command_set,
        command_set_config,
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add our custom options to the pytest option parser."""
    parser.addoption(
        "--no-old-git",
        action="store_true",
        default=False,
        help="Test with old git version.",
    )
    parser.addoption(
        "--no-old-hg",
        action="store_true",
        default=False,
        help="Test with old Mercurial version.",
    )


test_repo = fixture_union(
    "test_repo",
    [simple_repo, moved_file_repo, subfolder_repo, moved_file_subfolder_repo],
    scope="session",
)
"""All test repositories that will be used during tests."""


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: List[pytest.Item]
) -> None:
    """Discard certain test items according to the options passed."""
    discarded, kept = [], []
    for item in items:
        if hasattr(item, "callspec"):
            used_fixtures = [
                x.lstrip("/") for x in item.callspec.id.split("-")  # type:ignore
            ]
            no_old_git = (
                config.getoption("no_old_git") and "old_git_config" in used_fixtures
            )
            no_old_hg = (
                config.getoption("no_old_hg") and "old_hg_config" in used_fixtures
            )
            if no_old_git or no_old_hg:
                discarded.append(item)
                continue
        kept.append(item)
    items[:] = kept
    config.hook.pytest_deselected(items=discarded)
