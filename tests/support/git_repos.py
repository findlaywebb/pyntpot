"""A throwaway git repository for tests of the tooling that runs git.

`scratch_repo` makes one with a committed identity and no signing, so commits made in it
(by a test, or by the tool under test in a worktree of it) never read the user's git
identity or keys. `git` runs one command in it. It does not reach a network: a remote URL
set on the repository is never fetched unless a test asks.
"""

import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    """Run one git command in `repo` and return its stripped output."""
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def scratch_repo(root: Path) -> Path:
    """Make an empty repository at `root`, on branch `main`, and return it."""
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--quiet", "--initial-branch=main")
    for key, value in (
        ("user.name", "Tooling Test"),
        ("user.email", "tooling-test@example.invalid"),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(root / ".no-hooks")),
    ):
        git(root, "config", key, value)
    return root


def commit_all(repo: Path, message: str) -> str:
    """Stage every file in `repo`, commit it, and return the commit."""
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", message)
    return git(repo, "rev-parse", "HEAD")
