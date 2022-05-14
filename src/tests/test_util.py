"""Unit tests for :mod:`_docsweeper.util`."""
from __future__ import annotations

from pathlib import Path

import pytest
from pytest_cases import parametrize_with_cases

from _docsweeper.util import ExecutableError, call_subprocess


class _CasesCallSubProcessError:
    def case_happy(self) -> str:
        return "ls"

    @pytest.mark.xfail(raises=ExecutableError, strict=True)
    def case_nonexisting_executable(self) -> str:
        return "abcdef"

    @pytest.mark.xfail(raises=ExecutableError, strict=True)
    def case_nonexecutable_executable(
        self, tmpdir_factory: pytest.TempdirFactory
    ) -> str:
        path = Path(tmpdir_factory.mktemp("temp"))
        file_ = Path(path, "nonexec")
        file_.touch()
        return str(file_)


@parametrize_with_cases("command", cases=_CasesCallSubProcessError)
def test_call_subprocess_executable(command: str) -> None:
    """Test behavior of :func:`util.subprocess` with different executables."""
    call_subprocess([command])
