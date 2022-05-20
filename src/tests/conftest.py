"""Main test configuration and fixtures.

Provides the fixtures :func:`.simple_repo`, :func:`.moved_file_repo`. These fixtures
offer readymade repositories and corresponding helper classes via the
:class:`.Repository` instance variable. There is a fixture ``vcs_test_config`` that
provides all avaible repositories in succession to a single test function.

"""
from __future__ import annotations

import configparser
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Type

import pytest
from faker import Faker
from pytest_cases import fixture, fixture_union, parametrize

from _docsweeper.util import RevisionIdentifier, call_subprocess
from _docsweeper.version_control import (
    GitCommandSet,
    MercurialCommandSet,
    VCSCommandSet,
    VCSCommandSetConfig,
    command_sets,
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

    @abstractmethod
    def init(self, repository_path: Path) -> None:
        """Initialize a repository at *repository_path*."""

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
    """A temporary test repository in the file system."""

    repository_path: Path
    """Path of the repository in the file system."""
    revisions: List[Tuple[str, Path]]
    """List of revision lists and test files.

    A list of tuples, each consisting of a revision identifier, and the name of a file
    in this revision.

    """
    vcs_command_set_type: Type[VCSCommandSet]
    """Type of version control used."""
    vcs_command_set_config: VCSCommandSetConfig
    """Config. Only the attribute *executable* is set."""
    helper: _VCSHelper


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
    if not user_config.has_option(section, option):
        return ""
    return user_config.get(section, option)


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
    [git_config, hg_config],
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
                file_name.as_posix(),
            ],
            cwd=repository_path,
        )
        return result.splitlines()

    def add_file(self, code_file: Path, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "add", code_file.as_posix()],
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
                f"{revision}:{file_name.as_posix()}",
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
            [
                str(self.executable),
                "mv",
                f"{file_from.as_posix()}",
                f"{file_to.as_posix()}",
            ],
            cwd=repository_path,
        )

    def commit(self, message: str, repository_path: Path) -> None:
        call_subprocess(
            [str(self.executable), "commit", "-m", message],
            cwd=repository_path,
        )

    def init(self, repository_path: Path) -> None:
        call_subprocess([str(self.executable), "init", str(repository_path)])


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

    def init(self, repository_path: Path) -> None:
        call_subprocess([str(self.executable), "init", str(repository_path)])


@fixture(scope="session")
@parametrize("config", [git_config, hg_config], scope="session")
def simple_repo(
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    config: CommandSetTestConfig,
) -> Repository:
    """Return simple repository fixture containing only a single file."""
    return _build_simple_repo(
        config, f"simple_{config[0].name}_repo", tmpdir_factory, faker
    )


@fixture(scope="session")
@parametrize("config", [git_config, hg_config], scope="session")
def subfolder_repo(
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    config: CommandSetTestConfig,
) -> Repository:
    """Return a repository fixture containing a file in a subfolder."""
    return _build_simple_repo(
        config,
        f"subfolder_{config[0].name}_repo",
        tmpdir_factory,
        faker,
        Path("subfolder", faker.file_name(extension=".py")),
    )


@fixture(scope="session")
@parametrize("config", [git_config, hg_config], scope="session")
def moved_file_repo(
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    config: CommandSetTestConfig,
) -> Repository:
    """Return a repository fixture  with a file that has been moved at some point."""
    return _build_moved_file_repo(
        config, f"moved_file_{config[0].name}_repo", tmpdir_factory, faker
    )


@fixture(scope="session")
@parametrize("config", [git_config, hg_config], scope="session")
def moved_file_subfolder_repo(
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    config: CommandSetTestConfig,
) -> Repository:
    """Return a repository fixture that contains in a subfolder that has been moved."""
    return _build_moved_file_repo(
        config,
        f"moved_file_{config[0].name}_repo",
        tmpdir_factory,
        faker,
        Path("subfolder", "code.py"),
    )


@pytest.fixture(scope="session")
def faker() -> Faker:
    """Return a session-scoped faker instance.

    The default faker fixture is function-scoped and can not be used
    in higher-scoped fixtures.

    :returns: the faker fixture
    """
    return Faker()


def _build_moved_file_repo(
    config: CommandSetTestConfig,
    repo_name: str,
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    code_file_path: Optional[Path] = None,
) -> Repository:
    """Return a repository fixture  with a file that has been moved at some point."""

    basic_repo = _build_simple_repo(
        config, repo_name, tmpdir_factory, faker, code_file_path
    )
    code_file = basic_repo.revisions[0][1]
    repository_path = basic_repo.repository_path
    destination_file = repository_path.joinpath(faker.file_name())
    helper = basic_repo.helper
    helper.move_file(repository_path, code_file, destination_file)
    helper.commit("moved file.", repository_path)

    new_content = """def test_function():
    \"\"\"test a function\"\"\"
    return 6"""
    helper.write_and_commit_content(
        destination_file, new_content, "Changed code.", repository_path
    )
    revisions = basic_repo.revisions
    new_revisions = helper.get_revisions(repository_path, destination_file)[:2]
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
        basic_repo.vcs_command_set_type,
        basic_repo.vcs_command_set_config,
        helper,
    )


def _build_simple_repo(
    config: CommandSetTestConfig,
    repo_name: str,
    tmpdir_factory: pytest.TempdirFactory,
    faker: Faker,
    code_file_path: Optional[Path] = None,
) -> Repository:
    repository_path = Path(tmpdir_factory.mktemp(repo_name))
    vcs_command_set, vcs_config, _ = config
    assert vcs_config.executable
    executable = vcs_config.executable
    helper = _helpers[vcs_command_set.name](executable)
    helper.init(repository_path)
    revisions = []

    code_file = repository_path.joinpath(
        code_file_path if code_file_path else Path(faker.file_name(extension="py"))
    )
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
        helper.write_and_commit_content(
            code_file, content, f"commit #{index}", repository_path
        )
    revisions = [
        (revision, code_file.relative_to(repository_path))
        for revision in helper.get_revisions(repository_path, code_file)
    ]
    return Repository(
        repository_path,
        revisions,
        vcs_command_set,
        VCSCommandSetConfig(executable=executable),
        helper,
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add our custom options to the pytest option parser."""
    parser.addoption(
        "--vcs",
        action="store",
        type=str,
        nargs="+",
        choices=command_sets.keys(),
        default=list(command_sets.keys()),
        help="List of version control systems to run tests for.",
    )
    parser.addoption(
        "--no-vcs",
        action="store_true",
        default=False,
        help="Do not test any version control systems.",
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
    vcs_used = [] if config.getoption("no_vcs") else config.getoption("vcs")
    for item in items:
        item_discarded = False
        if hasattr(item, "callspec"):
            for vcs in command_sets.keys():
                if vcs not in vcs_used:
                    used_fixtures = [
                        x.lstrip("/")
                        for x in item.callspec.id.split("-")  # type:ignore
                    ]
                    if f"{vcs}_config" in used_fixtures:
                        discarded.append(item)
                        item_discarded = True
                        break
        if not item_discarded:
            kept.append(item)
    items[:] = kept
    config.hook.pytest_deselected(items=discarded)


_helpers = {"git": _GitHelper, "hg": _MercurialHelper}
