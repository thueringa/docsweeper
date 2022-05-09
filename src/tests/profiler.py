"""Profiling suite for Docsweeper."""
import cProfile
import pstats
import tempfile
from pathlib import Path

from _docsweeper.docsweeper import analyze_file
from _docsweeper.util import call_subprocess
from _docsweeper.version_control import GitCommandSet, VCSCommandSetConfig


def _prepare_run() -> tempfile.TemporaryDirectory:  # type:ignore
    repo_dir = tempfile.TemporaryDirectory()
    call_subprocess(
        [
            "/usr/bin/git",
            "clone",
            "https://github.com/aibasel/lab.git",
            str(repo_dir.name),
        ]
    )
    return repo_dir


if __name__ == "__main__":
    profiler = cProfile.Profile()
    repo_dir = _prepare_run()
    profiler.enable()
    analyze_file(
        GitCommandSet,
        VCSCommandSetConfig(executable=Path("/usr/bin/git"), follow_rename=True),
        Path(repo_dir.name, "lab", "experiment.py"),
    )
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    print("Statistics for version control module:")
    stats.print_stats(
        "version_control.py:.*(vcs_root|get_(all_revisions|file_from_repo|old_name))"
    )
    print("Statistics for docsweeper module:")
    stats.print_stats("docsweeper.py")
