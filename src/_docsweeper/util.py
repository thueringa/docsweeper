"""General utility functions."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, Generic, Hashable, List, Optional, TypeVar

logger = logging.getLogger(__name__)

RevisionIdentifier = str
"""Type alias for a revision identifier."""


class ExecutableError(Exception):
    """Raised when the executable is not found or is not executable."""

    executable: str

    def __init__(self, executable: str):
        """Raise an error that denotes a problem with *executable*."""
        self.executable = executable
        super().__init__(f"Invalid executable {executable}")


def call_subprocess(command: List[str], cwd: Optional[Path] = None) -> str:
    """Wrap calls to :func:`subprocess.run`.

    The parameters *command* and *cwd* are passed on to :func:`subprocess.run` and must
    adhere to the preconditions described there.

    :param command: The command as specified by the interface of :func:`subprocess.run`.
    :param cwd: The directory to change to for executing the command. If `None`, then
        the current directory is used.
    :raises subprocess.CalledProcessError: The underlying process has exited
        with a non-zero exit code.
    :raises ExecutableError: when the command passed to :func:`subprocess.run` is not
        found or is otherwise not executable
    :returns: The text that was written to standard output by running the command.

    """
    logger.debug(f'Running command {" ".join(command)} in directory {cwd}')
    try:
        result = subprocess.run(
            command, cwd=cwd, check=True, capture_output=True, text=True
        )
    except (OSError) as exception:
        raise ExecutableError(command[0]) from exception
    return result.stdout


def read_file(path: Path) -> str:
    """Read the file *path* to memory and return its contents.

    :param path: path of the file
    :raises OSError: There has been an issue opening the file.
    :raises ValueError: There is an encoding issue with the file.
    :returns: The contents of *path*.

    """
    with open(path) as file_handle:
        return file_handle.read()


K = TypeVar("K", bound=Hashable)
"""Generic type variable for a type that supports :class:`typing.Hashable`."""
V = TypeVar("V")
"""Generic type variable for any object."""


class Cache(Generic[K, V]):
    """
    A generic key-value cache for any object type.

    The key must be hashable, as a dictionary is used as the underlying data type.
    """

    _data: Dict[K, V]

    def __init__(self) -> None:
        """Instantiate the cache."""
        self._data = {}

    def get(self, key: K) -> Optional[V]:
        """Return item with key *key*.

        :param key: key of the desired item
        :returns: the item or ``None`` if there is no item with key *key* in the cache

        """
        return self._data[key] if key in self._data else None

    def put(self, key: K, value: V) -> None:
        """Put object *value* to cache with key *key*.

        :param key: the key
        :param value: the value

        """
        self._data[key] = value
