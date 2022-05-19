"""Main module for docsweeper functionality."""
from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Type, Union

from _docsweeper.util import Cache, RevisionIdentifier, read_file
from _docsweeper.version_control import (
    FileRenamedError,
    VCSCommandSet,
    VCSCommandSetConfig,
    VCSShim,
)

TokenHistory = Dict[str, "DocumentedToken"]

logger = logging.getLogger(__name__)


class ParserError(SyntaxError):
    """Raised when a code file could not be parsed."""

    def __init__(self, file_: Path, error: SyntaxError) -> None:
        """*file_* was not parseable due to underlying parser error  *error*."""
        message = (
            f"Could not parse file '{str(file_)}'. Reason: {error.msg}. "
            f"line number: {error.lineno}, text: '{error.text}'"
        )
        super().__init__(message)


class DocumentedToken(NamedTuple):
    """Data class for a python code token."""

    name: str
    """name of the code token"""
    docstring: str
    """docstring of the code token"""
    text: str
    """code of the token, with the docstring removed"""
    lineno: int
    """beginning line number"""
    end_lineno: int
    """ending line number"""


class DocumentedTokenStatistic(NamedTuple):
    """Statistics about the docstring history of a :class:`~.DocumentedToken`."""

    last_docstring_change: Optional[Tuple[RevisionIdentifier, int]]
    """A tuple consisting of the revision the docstring was last changed, and an integer
    depicting how many commits ago that was. ``None`` if the docstring has not ever been
    changed. """
    code_changes: int
    """How often the body of the token was changed since
    :attr:`.last_docstring_change`. """


def analyze_file(
    vcs_command_set_type: Type[VCSCommandSet],
    vcs_command_set_config: VCSCommandSetConfig,
    path: Path,
) -> List[Tuple[DocumentedToken, DocumentedTokenStatistic]]:
    """Analyzes code file at *path* and return its documented token statistics.

    :param vcs_command_set_type: type of the version control system to use
    :param vcs_command_set_config: version control configuration
    :param path: points to the code file in the file system
    :raises VCSExecutableError: if there is an unexpected error with the executable
        set in *vcs_command_set_config*
    :raises ParserError: if there is an unexpected error parsing *path*
    :returns: each entry of the list consists of the documented token, and its
        docstring history statistic

    """
    analyzer = _Analyzer(vcs_command_set_type, vcs_command_set_config, path)
    return analyzer.token_statistics


class _Analyzer:
    """Analyzes a code file for documented token statistics."""

    _history_cache: Cache[Tuple[RevisionIdentifier, Path], Dict[str, DocumentedToken]]
    """Cache for visited versions of a file."""
    _vcs_shim: VCSShim
    """Interface to the version control system."""
    token_statistics: List[Tuple[DocumentedToken, DocumentedTokenStatistic]]
    """Hold results of the docstring analysis."""

    def __init__(
        self,
        vcs_command_set_type: Type[VCSCommandSet],
        vcs_command_set_config: VCSCommandSetConfig,
        file_path: Path,
    ) -> None:
        self._vcs_shim = VCSShim(vcs_command_set_type, vcs_command_set_config)
        self._history_cache = Cache()
        documented_tokens = _get_documented_tokens(file_path)
        self.token_statistics = [
            (token, self._get_token_statistic(token, file_path))
            for token in documented_tokens.values()
        ]

    def _get_token_statistic(
        self, token: DocumentedToken, path: Path
    ) -> DocumentedTokenStatistic:
        """Return the token statistic for *token* in file *source_file*.

        :param token: the token
        :param path: path of the file in the file system
        :return: the statistic of *token*
        """
        logger.info(
            (
                f"Create history for token {token.name} "
                f"at line numbers {token.lineno},{token.end_lineno}"
            )
        )
        history = self._create_history(token, path)
        logger.info(f"History of {token.name} created successfully.")
        return DocumentedTokenStatistic(
            self._get_last_docstring_change(token, history),
            self._get_code_changes(history),
        )

    def _create_history(self, token: DocumentedToken, path: Path) -> TokenHistory:
        """Create a token history for *token*.

        A token history is a mapping between revision identifiers and the corresponding
        representation of *token* in each relevant revision.

        :param token: the token
        :param path: path of the containing file in the file system
        :return: the token history for *token*

        """
        history = {}

        revisions = self._vcs_shim.get_all_revisions(path)
        logger.info(f"Found {len(revisions)} revisions.")
        current_file_path = path
        for index, revision in enumerate(revisions):
            logger.info(f"Checking out revision {revision}.")
            file_ = self._history_cache.get((revision, current_file_path))
            if not file_:
                file_data = None
                try:
                    file_data = self._vcs_shim.get_file_from_repo(
                        current_file_path, revision
                    )
                except (FileRenamedError, ValueError):
                    old_path = self._vcs_shim.get_old_name(
                        current_file_path, revisions[index - 1]
                    )
                    if not old_path:
                        logger.info(
                            f"lost track of file {current_file_path} in revision "
                            f"{revision}"
                        )
                        break
                    current_file_path = Path(
                        self._vcs_shim.vcs_root(current_file_path), old_path
                    )
                    file_data = self._vcs_shim.get_file_from_repo(
                        current_file_path, revision
                    )
                try:
                    file_ = _get_documented_tokens(
                        current_file_path,
                        data=file_data,
                    )
                    self._history_cache.put((revision, current_file_path), file_)
                except SyntaxError:
                    logger.info(f"Could not parse file {path} from revision {revision}")
                    break
            if token.name not in file_.keys():
                logger.debug(
                    f"Token {token.name} is does not exist or is not commented "
                    f"in file {current_file_path} of revision {revision}"
                )
                break
            history_token = file_[token.name]
            history[revision] = history_token

            if history_token.docstring != token.docstring:
                break
        return history

    def _get_last_docstring_change(
        self, token: DocumentedToken, token_history: TokenHistory
    ) -> Optional[Tuple[RevisionIdentifier, int]]:
        """Return the last time the docstring of *token* was changed.

        :param token: the token
        :param token_history: the token history of *token*
        :return: a tuple consisting of the revision identifier that the docstring of
            *token* was last changed and an integer designating how many revisions ago
            that was. Return value is ``None`` if the docstring has never been changed.

        """
        for n, (revision, old_token) in enumerate(token_history.items()):
            if token.docstring != old_token.docstring:
                logger.debug(
                    f"Found last docstring change in revision {revision} "
                    f"({n} revisions ago)."
                )
                return (revision, n)
        logger.debug("Did not find any changes of docstring in history.")
        return None

    def _get_code_changes(
        self, token_history: TokenHistory, since: Optional[RevisionIdentifier] = None
    ) -> int:
        """Return how often the code body changed since the last change in its docstring.

        :param token_history: the token history
        :param since: limit search to ancestors after this revision
        :returns: amount of code changes since the last docstring change

        """
        revision_list = list(token_history.keys())
        if not revision_list:
            return 0
        if not since:
            since = revision_list[-1]
        revisions = revision_list[
            : revision_list.index(since)
            if since is not None
            else len(revision_list) - 1
        ]
        revisions.reverse()

        num_changed = 0
        current_token = token_history[since]
        for revision in revisions:
            new_token = token_history[revision]
            if new_token.text != current_token.text:
                num_changed += 1
            current_token = new_token
        return num_changed


def _get_documented_tokens(
    path: Path, data: Optional[str] = None
) -> Dict[str, DocumentedToken]:
    """Return all document tokens that occur in *path*.

    :param path: the path of the python code
    :param data: if set, do not read python code from *path* and use *data* instead
    :raises ParserError: if *path* is not parseable
    :returns: a dictionary that maps the name of each token to its parsed
        `DocumentedToken` object

    """
    visitor = _DocumentedTokenVisitor(path, data)
    return visitor.documented_tokens


class _DocumentedTokenVisitor(ast.NodeVisitor):
    """Retrieve all documented tokens from a python code file."""

    documented_tokens: Dict[str, DocumentedToken]

    def __init__(self, path: Path, data: Optional[str] = None) -> None:
        """Retrieve all documented tokens of the code in *path*.

        After completion of this function, the documented tokens can be accessed via the
        attribute :attr:`.documented_tokens`.

        :param path: the path of the python code
        :param data: if set, do not read python code from *path* and use *data* instead
        :raises ParserError: if *path* is not parseable
        """
        if data is None:
            data = read_file(path)

        self._data = data
        self._lines = self._data.splitlines()
        self._current_name = [path.stem]
        self.documented_tokens = {}
        try:
            root_node = ast.parse(data, filename=path.name)
        except SyntaxError as exception:
            raise ParserError(path, exception) from exception
        self.generic_visit(root_node)
        del self._data
        del self._current_name
        del self._lines

    def generic_visit(self, node: ast.AST) -> None:
        """Visit code token *node*.

        When visiting *node*:
        - keep track of the current fully qualified token name
        - handle the docstring of *node* if it exists, and
        - visit all child nodes of *node*.

        :param node: the token that is visited

        """
        has_name = hasattr(node, "name")
        if has_name:
            self._current_name.append(node.name)  # type:ignore
        if isinstance(
            node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module)
        ):
            self._handle_potentially_documented_token(node)
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.generic_visit(item)
            elif isinstance(value, ast.AST):
                self.generic_visit(value)
        if has_name:
            self._current_name.pop()

    def _get_source(
        self,
        node: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module],
    ) -> str:
        """Return the source code that belongs to *node*.

        :func:`ast.get_source_segment` is very slow, this is much faster when called
        repeatedly.

        :param node: the token for which the source code shall be returned
        :returns: the source code of *node*. Return `None` if there is no source.
        """
        source = self._lines[node.lineno - 1 : self._get_end_lineno(node)]
        return "\n".join(source)

    def _get_end_lineno(
        self,
        node: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module],
    ) -> int:
        """Return the ending line number of *node*.

        Python 3.7 does not have the :attr:`ast.AST.end_lineno` attribute. Instead, this
        function returns the line number of the last element of the body of *node*. For
        Python 3.8 and upwards, :attr:`ast.AST.end_lineno` is returned directly.

        :param node: the node
        :returns: the ending line number

        """
        return (
            node.body[-1].lineno
            if sys.version_info < (3, 8) or node.end_lineno is None
            else node.end_lineno
        )

    def _handle_potentially_documented_token(
        self,
        node: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module],
    ) -> None:
        """Append *node* to :attr:`.documented_tokens` if it has a docstring.

        :param node: the node

        """
        docstring = ast.get_docstring(node)
        if docstring is None:
            return
        if isinstance(node, ast.Module):
            combined_name = ".".join(self._current_name)
            source = ""
            lineno = 0
            end_lineno = len(self._lines)
        else:
            combined_name = ".".join(self._current_name[1:])
            source = self._get_source(node)
            lineno = node.lineno
            end_lineno = self._get_end_lineno(node)
        self.documented_tokens[combined_name] = DocumentedToken(
            combined_name,
            docstring,
            source.replace(docstring, ""),
            lineno,
            end_lineno,
        )
