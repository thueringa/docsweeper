"""Result handlers for docstring analysis results.

Provides result handlers that write the results of a token analysis into some output
stream, like stdout.

"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import List, TextIO

import click

from _docsweeper.docsweeper import DocumentedToken, DocumentedTokenStatistic


class AbstractResultHandler(ABC):
    """Result handler that is agnostic as to how the handled entries are formatted.

    Subclasses must implement :meth:`~.AbstractResultHandler._format_result` so that
    entries are formatted, or inherit from a class that already provides such a
    formatter.

    Output streams can be added to the result handler by calling
    :meth:`~.AbstractResultHandler.add_stream`.

    """

    _streams: List[TextIO]
    """The streams that this result handler outputs to."""

    def __init__(self) -> None:
        """Instantiate the result handler."""
        self._streams = []

    def handle_result(
        self, file_name: str, token: DocumentedToken, history: DocumentedTokenStatistic
    ) -> None:
        """Pass the result of the token analysis to the underlying output stream.

        Performs the necessary formatting of input variables and writes the result entry
        to and output stream.

        :param file_name: path of the file that was analyzed
        :param token: the token
        :param history: the analysis results that belong to `token`

        """
        for handler in self._streams:
            handler.write(self._format_result(file_name, token, history))

    @abstractmethod
    def _format_result(
        self, file_name: str, token: DocumentedToken, history: DocumentedTokenStatistic
    ) -> str:
        """Format the analysis data.

        :param file_name: path of the file that was analyzed
        :param token: the token
        :param history: the analysis results that belong to `token`

        """
        pass

    def add_stream(self, stream: TextIO) -> None:
        """Append `stream` to the streams that this result handler outputs to.

        :param stream: the stream

        """
        self._streams.append(stream)


class HumanReadableStringResultHandler(AbstractResultHandler):
    """Formats values in relatively verbose human-readable strings.

    Suited for output in a console terminal.

    """

    def _format_result(
        self, file_name: str, token: DocumentedToken, history: DocumentedTokenStatistic
    ) -> str:
        ret = [f"{file_name}:{token.name}\n", "\tlast docstring change: "]
        if history.last_docstring_change is None:
            ret.append("never changed since creation\n")
        else:
            ret.append(
                f"{history.last_docstring_change[1]} revision"
                f"{'s' if history.last_docstring_change[1] != 1 else ''} "
                f"ago, in revision {history.last_docstring_change[0]}\n"
            )
        ret.append(f"\tcode changes since: {history.code_changes}\n")
        return "".join(ret)


class ClickResultHandler(HumanReadableStringResultHandler):
    """Handle results using :func:`click.echo`."""

    def handle_result(
        self, file_name: str, token: DocumentedToken, history: DocumentedTokenStatistic
    ) -> None:
        """Write result to standard output using :func:`click.echo`."""
        click.echo(self._format_result(file_name, token, history))

    def add_stream(self, stream: TextIO) -> None:
        """Not implemented for this result handler.

        :param stream: the stream to be added
        :raises NotImplementedError: when called

        """
        raise NotImplementedError


class StdOutResultHandler(HumanReadableStringResultHandler):
    """A result handler that outputs to standard output."""

    def __init__(self) -> None:
        """Instantiate the result handler.

        Adds the standard output stream to its output stream.

        """
        super().__init__()
        self.add_stream(sys.stdout)
