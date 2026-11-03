"""Run git for the golden diff tooling and its tests: one runner, used by every caller.

`git` runs one command in a repository and returns its stripped output, raising
`subprocess.CalledProcessError` (stderr captured) when git exits non-zero. `git_lines` is
the same, as non-empty lines. `is_commit` asks whether a ref names a commit, without raising.

It does not choose a repository, a remote or an identity: callers pass the repository, and
git reads its own configuration. It never passes `--force` or rewrites a ref by itself.
"""

import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    """Run one git command in `repo` and return its stripped output.

    Raises:
        subprocess.CalledProcessError: When git exits non-zero; its `stderr` holds git's message.
    """
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def git_lines(repo: Path, *args: str) -> list[str]:
    """Run one git command in `repo` and return its non-empty output lines."""
    return [line for line in git(repo, *args).splitlines() if line]


def is_commit(repo: Path, ref: str) -> bool:
    """Return whether `ref` names a commit in `repo`."""
    done = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return done.returncode == 0
