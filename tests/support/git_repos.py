"""Throwaway git repositories for tests of the tooling that runs git.

`scratch_repo` makes a working repository with a set identity and no signing, so commits
made in it (by a test, or by the tool under test in a worktree of it) never read the user's
git identity or keys. `bare_remote` makes a bare repository in a test's temporary directory
to stand in for `origin`, so a push really happens and lands nowhere else. Commands run
through `support.git_commands.git`. Nothing here reaches a network.
"""

from pathlib import Path

from support.git_commands import git


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


def bare_remote(root: Path) -> Path:
    """Make an empty bare repository at `root` that refuses non-fast-forward pushes; return it.

    It stands in for `origin`. Refusing non-fast-forward updates and deletions makes any
    force-push to it fail, so a test that pushes through it proves none was made.
    """
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--quiet", "--bare", "--initial-branch=main")
    git(root, "config", "receive.denyNonFastForwards", "true")
    git(root, "config", "receive.denyDeletes", "true")
    return root
