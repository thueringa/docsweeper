"""Module for version control functions."""
from __future__ import annotations

import logging
import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, NamedTuple, Optional, Tuple, Type, TypeVar

from _docsweeper.util import ExecutableError, RevisionIdentifier, call_subprocess

logger = logging.getLogger(__name__)


class VCSCommandSetConfig(NamedTuple):
    """Configuration values for :class:`~.VCSCommandSet`.

    Holds configuration values that are customizable by clients.

    """

    executable: Optional[Path] = None
    """The path of the executable of the version used."""
    follow_rename: Optional[bool] = None
    """Whether the version control system shall follow renamed files."""

    def merge(self, other: VCSCommandSetConfig) -> VCSCommandSetConfig:
        """Return a new config with merged values of this config and  *other*.

        :param other: entries that are not ``None`` in this config are merged into the
            new one
        :returns: the merged config

        """
        set_fields = {
            field: getattr(other, field)
            for field in other._fields
            if getattr(other, field) is not None
        }
        return self._replace(**set_fields)

    def is_complete(self) -> bool:
        """Return whether all entries of this config have a value."""
        return not (self.executable is None or self.follow_rename is None)


class FileRenamedError(ValueError):
    """Raised when a file was unexpectedly detected to have been renamed."""

    def __init__(self, path: Path, revision: str) -> None:
        """Instantiate the Error and construct and appropriate message.

        :param path: the path of a file
        :param revision: the revision in which *path* was not found

        """
        self.path = path
        self.revision = revision
        self.message = (
            f"{self.path} not found in revision {self.revision}. "
            "File may have been moved or renamed."
        )
        super().__init__(self.message)


class IncompleteConfigurationError(KeyError):
    """Raised when an incomplete configuration is unexpectedly encountered."""

    def __init__(self, key: str) -> None:
        """Key *key* is missing in configuration."""
        super().__init__(f"Missing configuration value {key}.")


class VCSExecutableError(Exception):
    """Raised when there is an issue with the chosen version control executable.

    For example, if the executable does not exist or is otherwise not executable.

    """

    def __init__(self, vcs: str, executable: str) -> None:
        """Raise an exception with *executable* for version control system *vcs*."""
        message = (
            f"{str(executable)} is not valid as an executable for version control "
            "system {vcs}"
        )
        super().__init__(message)


# ======================================
# Version Control Command API definition
# ======================================

_CommandError = TypeVar("_CommandError")
"""Generic type for the error of a :class:`_VCSCommand`."""
_CommandResult = TypeVar("_CommandResult")
"""Generic type for the result of a :class:`_VCSCommand`."""
_CommandArguments = TypeVar("_CommandArguments")
"""Generic type for the arguments of a :class:`_VCSCommand`."""


class _VCSCommand(ABC, Generic[_CommandError, _CommandResult, _CommandArguments]):
    """API for a version control command."""

    def __init__(self, executable: Path) -> None:
        """Initialize an instance of this command.

        :param executable: path of the version control system executable

        """
        self._executable: Path = executable

    @abstractmethod
    def tokenize_arguments(self, arguments: _CommandArguments) -> List[str]:
        """Tokenize arguments for use by :meth:`_docsweeper.util.call_subprocess`.

        For example, a tokenized version of the command `git init` would be `["git",
        "init"]`.

        :param arguments: dictionary of command tokens as provided by the client

        :return: A list of strings as specified by `subprocess.run`, representing the
            tokenized command that is called on the command line

        """
        pass

    @abstractmethod
    def handle_error(self, exception: subprocess.CalledProcessError) -> _CommandError:
        """Handle an error in command execution.

        :param exception: the exception that was raised during command execution.
        :return: some object that `~.handle_result` can act upon

        """
        pass

    @abstractmethod
    def handle_result(
        self, result: str, error: Optional[_CommandError], **kwargs: Any
    ) -> _CommandResult:
        """Handle the results of a command execution.

        :param result: the output of the command, as written to `stdout`
        :param error: error object generated by `~.handle_error`. `None`, if there has
            been no error during execution.
        :param **kwargs: any further arguments that are needed by the actual
            implementation
        :return: the processed result object

        """
        pass


class _HistoryCommandArguments(NamedTuple):
    """Arguments of :class:`_HistoryCommand`."""

    path: Path


class _HistoryCommand(
    _VCSCommand[None, List[RevisionIdentifier], _HistoryCommandArguments]
):
    def __init__(self, executable: Path, follow_rename: bool) -> None:
        super().__init__(executable)
        self._follow_rename = follow_rename


class _FileCommandArguments(NamedTuple):
    """Arguments of :class:`_FileCommand`."""

    revision: RevisionIdentifier
    path: Path
    repository_path: Path


class _FileCommand(_VCSCommand[None, str, _FileCommandArguments]):
    """Return the contents of *path* from a specific *revision*."""

    pass


class _PathCheckCommandArguments(NamedTuple):
    """Arguments of :class:`_PathCheckCommand`."""

    path: Path


class _PathCheckCommand(_VCSCommand[bool, bool, _PathCheckCommandArguments]):
    """Check if *path* is in version control."""

    pass


class _VCSRootCommandArguments(NamedTuple):
    """Argument dictionary for all args of :class:`_VCSRootCommand`."""

    path: Path


class _VCSRootCommand(_VCSCommand[None, str, _VCSRootCommandArguments]):
    """Return the root directory of the current version control repository."""

    pass


class _OldNameCommandArguments(NamedTuple):
    """Argument dictionary for all args of :class:`_OldNameCommand`."""

    revision: RevisionIdentifier
    path: Optional[Path]


class _OldNameCommand(_VCSCommand[None, Optional[Path], _OldNameCommandArguments]):
    """Return whether a file has been moved or renamed to *path* in *revision*."""

    pass


class VCSCommandSet(ABC):
    """Encapsulates all commands needed for a complete version control command set."""

    file_command: _FileCommand
    path_check_command: _PathCheckCommand
    vcs_root_command: _VCSRootCommand
    old_name_command: _OldNameCommand
    history_command: _HistoryCommand
    name: str

    def __init__(
        self,
        config: VCSCommandSetConfig,
    ) -> None:
        """Instantiate this version control command set according to the values in *config*.

        :param config: the configuration dictionary

        """

        pass


class GitCommandSet(VCSCommandSet):
    """An implementation of a version control command set for git."""

    class _GitHistoryCommand(_HistoryCommand):
        def tokenize_arguments(self, arguments: _HistoryCommandArguments) -> List[str]:
            path = arguments.path
            command_arr = [
                str(self._executable),
                "--no-pager",
                "log",
            ]
            if self._follow_rename:
                command_arr.append("--follow")
            command_arr.extend(["-s", "--format=%H", "--", path.name])
            return command_arr

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            pass

        @staticmethod
        def handle_result(
            result: str, error: Optional[_CommandError], **kwargs: Any
        ) -> List[RevisionIdentifier]:
            return result.splitlines()

    class _GitFileCommand(_FileCommand):
        def tokenize_arguments(self, arguments: _FileCommandArguments) -> List[str]:
            revision = arguments.revision
            path = arguments.path
            repository_path = arguments.repository_path
            relative_path = path.relative_to(repository_path)
            return [
                str(self._executable),
                "cat-file",
                "-p",
                f"{revision}:{relative_path.as_posix()}",
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            if exception.returncode == 128:
                # File was renamed or does not exist.
                raise ValueError() from exception
            raise exception from exception

        @staticmethod
        def handle_result(
            result: str,
            error: None,
            **kwargs: Any,
        ) -> str:
            return result.rstrip()

    class _GitPathCheckCommand(_PathCheckCommand):
        def tokenize_arguments(
            self, arguments: _PathCheckCommandArguments
        ) -> List[str]:
            path = arguments.path
            return [
                str(self._executable),
                "ls-files",
                "--error-unmatch",
                path.name,
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> bool:
            unknown_file_error = (
                exception.returncode == 1
                and "did not match any file(s) known to git" in exception.stderr
            )
            unknown_repo_error = exception.returncode == 128
            if unknown_file_error or unknown_repo_error:
                return True
            raise exception from exception

        @staticmethod
        def handle_result(result: str, error: Optional[bool], **kwargs: Any) -> bool:
            if error:
                return False
            return True

    class _GitVCSRootCommand(_VCSRootCommand):
        def tokenize_arguments(self, arguments: _VCSRootCommandArguments) -> List[str]:
            return [
                str(self._executable),
                "rev-parse",
                "--show-toplevel",
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            pass

        @staticmethod
        def handle_result(result: str, error: None, **kwargs: Any) -> str:
            return result.rstrip()

    class _GitOldNameCommand(_OldNameCommand):
        def tokenize_arguments(self, arguments: _OldNameCommandArguments) -> List[str]:
            revision = arguments.revision
            return [
                str(self._executable),
                "--no-pager",
                "diff-index",
                "-M",
                "--name-status",
                "--diff-filter=R",
                f"{revision}~1",
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            pass

        @staticmethod
        def handle_result(result: str, error: None, **kwargs: Any) -> Optional[Path]:
            path: Path = kwargs["path"]
            repository_path: Path = kwargs["repository_path"]
            relative_path: Path = path.relative_to(repository_path)
            pattern = re.compile(
                rf"^R\d+\W+(?P<old_name>.*?)\W+{re.escape(relative_path.as_posix())}$",
                re.MULTILINE,
            )
            match = re.search(pattern, result)
            return Path(match.group("old_name")) if match else None

    name: str = "git"

    def __init__(self, config: VCSCommandSetConfig) -> None:
        """Instantiate the git command set according to *config*."""
        executable = config.executable
        follow_rename = config.follow_rename
        assert executable is not None
        assert follow_rename is not None
        self.file_command = GitCommandSet._GitFileCommand(executable)
        self.path_check_command = GitCommandSet._GitPathCheckCommand(executable)
        self.vcs_root_command = GitCommandSet._GitVCSRootCommand(executable)
        self.old_name_command = GitCommandSet._GitOldNameCommand(executable)
        self.history_command = GitCommandSet._GitHistoryCommand(
            executable, follow_rename
        )


class MercurialCommandSet(VCSCommandSet):
    """An implementation of a version control command set for mercurial."""

    class _MercurialHistoryCommand(_HistoryCommand):
        def tokenize_arguments(self, arguments: _HistoryCommandArguments) -> List[str]:
            path = arguments.path
            command_arr = [
                str(self._executable),
                "--cwd",
                str(path if path.is_dir() else path.parent),
                "--pager=never",
                "log",
                "-T{node}\n",
            ]
            if self._follow_rename:
                command_arr.append("--follow")
            command_arr.append(path.name)
            return command_arr

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            if "cannot follow file not in parent revision" in exception.stderr:
                raise ValueError

        @staticmethod
        def handle_result(
            result: str, error: Any, **kwargs: Any
        ) -> List[RevisionIdentifier]:
            return result.splitlines()

    class _MercurialFileCommand(_FileCommand):
        def tokenize_arguments(self, arguments: _FileCommandArguments) -> List[str]:
            revision = arguments.revision
            repository_path = arguments.repository_path
            path = arguments.path

            relative_path = path.relative_to(repository_path)
            return [
                str(self._executable),
                "--pager=never",
                "cat",
                f"--rev={revision}",
                str(relative_path),
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            if (
                exception.returncode == 1 and "no such file in " in exception.stderr
            ) or (
                exception.returncode == 255 and "unknown revision" in exception.stderr
            ):
                # We always raise ValueError for mercurial because it does not
                # allow for easy following of renames. If no rename happened and the
                # file just does not exist, it will be caught later on in any case by
                # docsweeper.
                raise ValueError from exception
            raise exception from exception

        @staticmethod
        def handle_result(result: str, error: None, **kwargs: Any) -> str:
            return result.rstrip()

    class _MercurialPathCheckCommand(_PathCheckCommand):
        def tokenize_arguments(
            self, arguments: _PathCheckCommandArguments
        ) -> List[str]:
            path = arguments.path
            return [str(self._executable), "--pager=never", "cat", str(path)]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> bool:
            unknown_file_error = (
                exception.returncode == 1 and "no such file in " in exception.stderr
            )
            unknown_repo_error = exception.returncode == 255 and (
                "no repository found in " in exception.stderr
            )
            if unknown_file_error or unknown_repo_error:
                return True
            raise exception from exception

        @staticmethod
        def handle_result(result: str, error: Optional[bool], **kwargs: Any) -> bool:
            if error:
                return False
            return True

    class _MercurialVCSRootCommand(_VCSRootCommand):
        def tokenize_arguments(self, arguments: _VCSRootCommandArguments) -> List[str]:
            path = arguments.path
            return [
                str(self._executable),
                "--cwd",
                str(path if path.is_dir() else path.parent),
                "--pager=never",
                "root",
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            pass

        @staticmethod
        def handle_result(result: str, error: None, **kwargs: Any) -> str:
            return result.rstrip()

    class _MercurialOldNameCommand(_OldNameCommand):
        def tokenize_arguments(self, arguments: _OldNameCommandArguments) -> List[str]:
            revision = arguments.revision
            path = arguments.path
            if path is None:
                raise UnboundLocalError(
                    (
                        "'path' argument missing, but is required in "
                        "MercurialOldNameCommand"
                    )
                )
            return [
                str(self._executable),
                "--cwd",
                str(path if path.is_dir() else path.parent),
                "--pager=never",
                "log",
                "-p",
                "-g",
                f"--rev={revision}",
            ]

        @staticmethod
        def handle_error(
            exception: subprocess.CalledProcessError,
        ) -> None:
            pass

        @staticmethod
        def handle_result(result: str, error: None, **kwargs: Any) -> Optional[Path]:
            path = kwargs["path"]
            repository_path: Path = kwargs["repository_path"]
            relative_path: Path = path.relative_to(repository_path)
            pattern = re.compile(
                r"^rename from (?P<old_name>.*)$\n"
                rf"rename to {re.escape(relative_path.as_posix())}",
                re.MULTILINE,
            )
            match = re.search(pattern, result)
            old_name = Path(match.group("old_name")) if match else None
            return old_name

    name: str = "hg"

    def __init__(self, config: VCSCommandSetConfig) -> None:
        """Instantiate the Mercurial command set according to *config*."""
        executable = config.executable
        follow_rename = config.follow_rename

        assert executable is not None
        assert follow_rename is not None

        self.file_command = MercurialCommandSet._MercurialFileCommand(executable)
        self.path_check_command = MercurialCommandSet._MercurialPathCheckCommand(
            executable
        )
        self.vcs_root_command = MercurialCommandSet._MercurialVCSRootCommand(executable)
        self.old_name_command = MercurialCommandSet._MercurialOldNameCommand(executable)
        self.history_command = MercurialCommandSet._MercurialHistoryCommand(
            executable, follow_rename
        )


class VCSShim:
    """A shim between the output of a version control command set and clients.

    Encapsulates the low-level commands of a :class:`~VCSCommandSet` into a more
    user-friendly interface.

    """

    _vcs_command_set: VCSCommandSet
    """Instance of :class:`.VCSCommandSet` that is used."""
    _vcs_root: Optional[Path] = None
    """Cache for calls to :func:`~VCSShim.vcs_root`."""
    _revisions: Optional[List[RevisionIdentifier]] = None
    """Cache for calls to :func:`~VCSShim.get_all_revisions`."""

    def __init__(
        self,
        vcs_command_set: Type[VCSCommandSet],
        vcs_command_set_config: VCSCommandSetConfig,
    ) -> None:
        """Instantiate a :class:`VCSShim`.

        :param vcs_command_set: the :class:`~.VCSCommandSet` that is to be used
        :param vcs_command_set_config: configuration dictionary for the version control
            command set
        """
        self._vcs_command_set = vcs_command_set(vcs_command_set_config)

    def _call_command(
        self,
        command: _VCSCommand[_CommandError, _CommandResult, _CommandArguments],
        cwd: Optional[Path],
        command_arguments: _CommandArguments,
    ) -> _CommandResult:
        """Call *command* in *cwd* with *command_arguments* and return handled results.

        :param command: the command to be executed
        :param cwd: change working directory to this during execution. Do not change
            working directory if *cwd* is `None`.
        :param command_arguments: dictionary of arguments for the command
        :raises VCSExecutableError: if there is an issue with the chosen vcs executable
        :returns: the result of the command.
        """
        command_line_args = command.tokenize_arguments(command_arguments)
        try:
            result = call_subprocess(command_line_args, cwd)
            error = None
        except subprocess.CalledProcessError as exc:
            error = command.handle_error(exc)
            result = ""
        except ExecutableError as exception:
            raise VCSExecutableError(
                self._vcs_command_set.name, exception.executable
            ) from exception
        return command.handle_result(result, error)

    def vcs_root(self, path: Path) -> Path:
        """Return the repository root directory of *path*.

        This does not check whether *path* is actually under version control.

        :param path: the path of a file

        :returns: The repository root of *path*

        """

        # try cache:
        if self._vcs_root:
            return self._vcs_root

        # no cache hit, execute normally:
        while not path.exists():
            path = path.parent
        extra_arguments = _VCSRootCommandArguments(path=path)
        cwd_path = path if path.is_dir() else path.parent
        vcs_root = Path(
            self._call_command(
                self._vcs_command_set.vcs_root_command, cwd_path, extra_arguments
            )
        )
        self._vcs_root = vcs_root
        return vcs_root

    def _path_is_in_version_control(self, path: Path) -> bool:
        """Return whether *path* is under a version control system of the type used.

        :param path: the path of a file

        :returns: `True` if *path* is under version control, `False` otherwise

        """
        cwd_path = path if path.is_dir() else path.parent
        extra_arguments = _PathCheckCommandArguments(path=path)
        return self._call_command(
            self._vcs_command_set.path_check_command, cwd_path, extra_arguments
        )

    def get_all_revisions(
        self,
        path: Path,
    ) -> List[RevisionIdentifier]:
        """Return a list of revision identifiers in which the file *path* was changed.

        :param path: the path of a file in the repository
        :returns: a list of revision identifiers
        :raises ValueError: if *path* is not under version control

        """
        if self._revisions:
            return self._revisions
        if not self._path_is_in_version_control(path):
            raise ValueError(f"{path} does not seem to be under version control.")
        extra_arguments = _HistoryCommandArguments(path=path)
        cwd_path = path if path.is_dir() else path.parent
        revisions = self._call_command(
            self._vcs_command_set.history_command,
            cwd_path,
            extra_arguments,
        )
        self._revisions = revisions
        return revisions

    def get_file_from_repo(self, path: Path, revision: RevisionIdentifier) -> str:
        """Return the contents of *path* under *revision*.

        :param path: the path of a file in the repository
        :param revision: an identifier for a specific revision, eg a commit hash
        :raises RuntimeError: if the underlying version control command fails
            unexpectedly
        :raises ValueError: if *path* or *revision* is the empty string
        :returns: the file content

        """
        try:
            for var, var_name in [(revision, "revision"), (path, "path")]:
                if var == "":
                    raise ValueError(f"{var_name} may not be empty.")
            repository_path = self.vcs_root(path)
            extra_arguments = _FileCommandArguments(
                revision=revision, path=path, repository_path=repository_path
            )

            result = self._call_command(
                self._vcs_command_set.file_command, repository_path, extra_arguments
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError from exc
        return result

    def get_old_name(self, path: Path, revision: RevisionIdentifier) -> Optional[Path]:
        """If a file has been renamed to *path* in *revision*, return this files' old name.

        :param path: a path in the repository
        :param revision: a revision identifier
        :return: The old name of *path* in revision *revision* if it has been renamed \
            in this revision. Returns 'None' otherwise.
        """
        tokens = self._vcs_command_set.old_name_command.tokenize_arguments(
            _OldNameCommandArguments(revision=revision, path=path)
        )
        cwd_path = path if path.is_dir() else path.parent
        result = call_subprocess(tokens, cwd_path)
        return self._vcs_command_set.old_name_command.handle_result(
            result, None, path=path, repository_path=self.vcs_root(path)
        )


#: Dictionary of all supported command sets and their default configuration.
command_sets: Dict[str, Tuple[Type[VCSCommandSet], VCSCommandSetConfig]] = {
    "git": (
        GitCommandSet,
        VCSCommandSetConfig(executable=Path("/usr/bin/git"), follow_rename=True),
    ),
    "hg": (
        MercurialCommandSet,
        VCSCommandSetConfig(executable=Path("/usr/bin/hg"), follow_rename=True),
    ),
}
