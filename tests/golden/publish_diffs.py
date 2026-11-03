"""Commit review images to the `pr-assets` branch and write the Markdown block for a PR body.

Run from the repository root, after `diff_images.py`, as
`PYTHONPATH=tests uv run python tests/golden/publish_diffs.py OUT [--pr-branch NAME] [--push]`.
`OUT` is a `diff_images.py` output directory; `--pr-branch` defaults to the branch checked
out. It fetches `pr-assets` from `--remote` (default `origin`), builds one commit on the
fetched tip (or a parentless one when the remote has no `pr-assets` yet) whose tree is that
tip's with `<pr-branch>/` replaced by a copy of `OUT`, and, only with `--push`, pushes it to
`refs/heads/pr-assets` as a fast-forward. It writes `OUT/pr-body.md` and logs it: the summary
table and each image's review images, ready to paste into the PR body. Without `--push` it
is a dry run: the same commit is built but not pushed, so its links do not resolve yet.

Links are `raw.githubusercontent.com` URLs (the repository is public) naming the
`pr-assets` commit, not the branch, so a PR body keeps showing the review images it was
written with after a later publish, and no cache serves an older one. The owner and
repository come from the remote's configured URL.

Invariants: the working tree, the index, the checked-out branch and every local branch
are never touched; no local `pr-assets` branch is made, only the remote-tracking ref the
fetch updates. The commit is built in a detached temporary `git worktree`, removed
afterwards whatever happened. The push is never forced: when another publish moved the
remote tip first, the push is refused, and the publish fetches again and rebuilds on the new
tip, up to `PUSH_ATTEMPTS` times, then stops with an error. Commit and push skip the
repository's hooks, which check code, and `pr-assets` holds none. Exit codes: 0 when
published (or built, in a dry run), 2 when `OUT` holds no summary, the PR branch name is
unusable, or a git step or the push fails.
"""

import argparse
import contextlib
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from golden.diff_images import SUMMARY_JSON
from golden.diff_report import Summary, markdown

from support import REPO_ROOT
from support.git_commands import git

logger = logging.getLogger("publish_diffs")

#: The orphan branch that holds every PR's review images.
ASSETS_BRANCH = "pr-assets"

#: The Markdown block written beside the review images.
PR_BODY = "pr-body.md"

#: How many times a publish builds and pushes before a remote that keeps moving stops it.
PUSH_ATTEMPTS = 3

_GITHUB_REMOTE = re.compile(r"github\.com[:/](?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?/?$")


class PublishError(RuntimeError):
    """The review images were not published: the push was refused or kept losing a race."""


class _PushRefusedError(Exception):
    """The push of a built commit was refused; `stderr` holds git's reason."""

    def __init__(self, stderr: str) -> None:
        super().__init__(stderr)
        self.stderr = stderr


def github_slug(remote_url: str) -> str:
    """Return `owner/repo` from a GitHub remote URL, HTTPS or SSH.

    Raises:
        ValueError: When the URL is not a GitHub repository's.
    """
    found = _GITHUB_REMOTE.search(remote_url.strip())
    if found is None:
        raise ValueError(f"not a GitHub remote: {remote_url}")
    return str(found["slug"])


def asset_url(slug: str, commit: str, path: str) -> str:
    """Return the `raw.githubusercontent.com` link to one file of a `pr-assets` commit.

    Args:
        slug: The repository, as `owner/repo`.
        commit: The `pr-assets` commit holding the file.
        path: The file's path in that commit, with `/` separators; each segment is quoted.

    Returns:
        The URL.
    """
    quoted = "/".join(quote(part) for part in PurePosixPath(path).parts)
    return f"https://raw.githubusercontent.com/{slug}/{commit}/{quoted}"


def assets_dir(pr_branch: str) -> str:
    """Return the directory on `pr-assets` that holds one PR branch's review images.

    Raises:
        ValueError: When a `/`-separated segment of the name is empty, `.` or `..` (so an
            empty or absolute name too), or the name is `HEAD` (no branch is checked out).
    """
    parts = pr_branch.split("/")
    if pr_branch == "HEAD" or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unusable PR branch name: {pr_branch!r}")
    return pr_branch


def remote_tip(repo: Path, remote: str) -> str | None:
    """Fetch the remote's `pr-assets` and return its tip commit, or `None` when it has none.

    The fetch updates only the remote-tracking ref `refs/remotes/<remote>/pr-assets`.
    """
    head = f"refs/heads/{ASSETS_BRANCH}"
    if not git(repo, "ls-remote", remote, head):
        return None
    tracking = f"refs/remotes/{remote}/{ASSETS_BRANCH}"
    git(repo, "fetch", "--quiet", "--no-tags", remote, f"+{head}:{tracking}")
    return git(repo, "rev-parse", f"{tracking}^{{commit}}")


def _remove_worktree(repo: Path, worktree: Path) -> None:
    """Remove a temporary worktree; never raise, so an error that ended the publish shows."""
    try:
        git(repo, "worktree", "remove", "--force", str(worktree))
    except subprocess.CalledProcessError:
        shutil.rmtree(worktree, ignore_errors=True)
        with contextlib.suppress(subprocess.CalledProcessError):
            git(repo, "worktree", "prune")


def _build_and_push(
    repo: Path, out: Path, pr_branch: str, base: str | None, remote: str | None
) -> str:
    """Build the commit on `base` in a detached temporary worktree; push it when `remote` is set.

    Returns:
        The commit: `base` itself when `OUT` matches what `base` holds, so nothing is pushed.

    Raises:
        _PushRefusedError: When the remote refuses the push.
    """
    with tempfile.TemporaryDirectory() as tmp:
        worktree = Path(tmp) / ASSETS_BRANCH
        try:
            tree = _staged_tree(repo, worktree, out, assets_dir(pr_branch), base)
            if base is not None and tree == git(repo, "rev-parse", f"{base}^{{tree}}"):
                return base
            parents = [] if base is None else ["-p", base]
            message = f"Review images for {pr_branch}"
            commit = git(worktree, "commit-tree", tree, *parents, "-m", message)
            git(worktree, "update-ref", "--no-deref", "HEAD", commit)
            if remote is not None:
                _push(worktree, remote)
            return commit
        finally:
            _remove_worktree(repo, worktree)


def _staged_tree(repo: Path, worktree: Path, out: Path, target: str, base: str | None) -> str:
    """Add a detached worktree, stage `base`'s tree with `target/` replaced by `out`; return it.

    Only the index is filled from `base`: other PRs' files are never written out. The add is
    forced, so no ignore rule (the user's global excludes among them) drops a review image.
    """
    add = ["worktree", "add", "--quiet", "--detach", "--no-checkout", str(worktree)]
    git(repo, *add, "HEAD" if base is None else base)
    git(worktree, "read-tree", *(["--empty"] if base is None else [base]))
    git(worktree, "rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "--", target)
    shutil.copytree(out, worktree / target, ignore=shutil.ignore_patterns(PR_BODY))
    git(worktree, "add", "--all", "--force", "--", target)
    return git(worktree, "write-tree")


def _push(worktree: Path, remote: str) -> None:
    """Push the worktree's `HEAD` to the remote's `pr-assets`, fast-forward only.

    Raises:
        _PushRefusedError: When the remote refuses the push.
    """
    try:
        git(worktree, "push", "--quiet", "--no-verify", remote, f"HEAD:refs/heads/{ASSETS_BRANCH}")
    except subprocess.CalledProcessError as exc:
        raise _PushRefusedError(str(exc.stderr).strip()) from exc


def commit_assets(
    repo: Path,
    out: Path,
    pr_branch: str,
    remote: str,
    *,
    push: bool,
    attempts: int = PUSH_ATTEMPTS,
) -> str:
    """Build the commit holding `out` under `<pr_branch>/` on the remote's `pr-assets`; push when asked.

    Args:
        repo: The repository.
        out: The `diff_images.py` output directory.
        pr_branch: The PR branch the review images belong to.
        remote: The remote fetched from and pushed to.
        push: Whether to push the commit; without it the commit is built but not pushed.
        attempts: How many times to fetch, build and push before a moving remote stops it.

    Returns:
        The `pr-assets` commit holding the review images (the remote's tip when nothing changed).

    Raises:
        PublishError: When the push is refused with the remote tip unmoved, or the tip moved
            before every one of `attempts` pushes.
    """
    assets_dir(pr_branch)
    for _attempt in range(attempts):
        base = remote_tip(repo, remote)
        try:
            return _build_and_push(repo, out, pr_branch, base, remote if push else None)
        except _PushRefusedError as exc:
            if remote_tip(repo, remote) == base:
                raise PublishError(f"{remote} refused the push: {exc.stderr}") from exc
            logger.warning("%s's %s moved during the publish; rebuilding", remote, ASSETS_BRANCH)
    raise PublishError(f"{remote}'s {ASSETS_BRANCH} moved before each of {attempts} pushes")


def pr_body(summary: Summary, slug: str, commit: str, target: str) -> str:
    """Return the PR body's Markdown block for review images committed at `commit` under `target`."""
    return markdown(summary, lambda path: asset_url(slug, commit, f"{target}/{path}"))


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Publish review images for a PR body.")
    parser.add_argument("out", type=Path, metavar="OUT", help="a diff_images.py output directory")
    parser.add_argument("--pr-branch", default=None, help="the PR branch (default: checked out)")
    parser.add_argument("--remote", default="origin", help="the remote (default: origin)")
    parser.add_argument("--push", action="store_true", help=f"push {ASSETS_BRANCH} to the remote")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Publish and log the PR body; return 0 when published or built, 2 when something stops it."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    summary_path = args.out / SUMMARY_JSON
    if not summary_path.is_file():
        logger.error("no %s in %s: run diff_images.py first", SUMMARY_JSON, args.out)
        return 2
    try:
        pr_branch = args.pr_branch or git(args.repo, "rev-parse", "--abbrev-ref", "HEAD")
        slug = github_slug(git(args.repo, "config", "--get", f"remote.{args.remote}.url"))
        commit = commit_assets(args.repo, args.out, pr_branch, args.remote, push=args.push)
    except (ValueError, PublishError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else exc
        logger.error("not published: %s", detail)  # noqa: TRY400 (the reason is the whole message)
        return 2
    body = pr_body(Summary.from_json(summary_path.read_text()), slug, commit, assets_dir(pr_branch))
    (args.out / PR_BODY).write_text(body)
    if args.push:
        logger.info(
            "%s commit %s for %s, pushed to %s", ASSETS_BRANCH, commit, pr_branch, args.remote
        )
    else:
        logger.warning(
            "dry run: built %s commit %s but did not push it, so these links are not live yet; "
            "publish with --push",
            ASSETS_BRANCH,
            commit,
        )
    logger.info("PR body block (also in %s):\n\n%s", args.out / PR_BODY, body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
