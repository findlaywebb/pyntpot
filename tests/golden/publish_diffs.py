"""Commit diff images to the `pr-assets` branch and write the Markdown block for a PR body.

Run from the repository root, after `diff_images.py`, as
`PYTHONPATH=tests uv run python tests/golden/publish_diffs.py OUT [--pr-branch NAME] [--push]`.
`OUT` is a `diff_images.py` output directory; `--pr-branch` defaults to the branch checked
out. It copies `OUT` to `<pr-branch>/` on the orphan branch `pr-assets` (replacing what an
earlier publish of that PR left there), commits it, pushes `pr-assets` to `--remote`
(default `origin`) only when given `--push`, writes `OUT/pr-body.md` and logs it: the
summary table and each image's review images, ready to paste into the PR body.

Links name the `pr-assets` commit, not the branch, so a PR body keeps showing the review
images it was written with after a later publish, and no cache serves an older one. The
repository is public, so links are `raw.githubusercontent.com` URLs; `--url-form blob` writes
`github.com/<owner>/<repo>/blob/<commit>/<path>?raw=true` links, which render for a reader
signed in to a private repository. The owner and repository come from the remote's URL.

Invariants: the working tree, the index and the checked-out branch are never touched. The
commit is made in a temporary `git worktree` of `pr-assets` (created as an orphan with no
files the first time), which is removed afterwards; the commit and the push skip the
repository's hooks, which check code and `pr-assets` holds none. A local `pr-assets`
behind the remote's is fast-forwarded first; one that has diverged stops the publish. Exit codes: 0 when
published, 2 when `OUT` holds no summary, the PR branch name is unusable or a git step fails.
"""

import argparse
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

logger = logging.getLogger("publish_diffs")

#: The orphan branch that holds every PR's diff images.
ASSETS_BRANCH = "pr-assets"

#: The Markdown block written beside the review images.
PR_BODY = "pr-body.md"

_GITHUB_REMOTE = re.compile(r"github\.com[:/](?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?/?$")


def github_slug(remote_url: str) -> str:
    """Return `owner/repo` from a GitHub remote URL, HTTPS or SSH.

    Raises:
        ValueError: When the URL is not a GitHub repository's.
    """
    found = _GITHUB_REMOTE.search(remote_url.strip())
    if found is None:
        raise ValueError(f"not a GitHub remote: {remote_url}")
    return str(found["slug"])


def asset_url(slug: str, commit: str, path: str, form: str = "raw") -> str:
    """Return the link to one file of the `pr-assets` commit, each path segment quoted.

    Args:
        slug: The repository, as `owner/repo`.
        commit: The `pr-assets` commit holding the file.
        path: The file's path in that commit, with `/` separators.
        form: `raw` for a `raw.githubusercontent.com` URL, `blob` for a `?raw=true` one.

    Returns:
        The URL.
    """
    quoted = "/".join(quote(part) for part in PurePosixPath(path).parts)
    if form == "blob":
        return f"https://github.com/{slug}/blob/{commit}/{quoted}?raw=true"
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


def _git(repo: Path, *args: str) -> str:
    """Run one git command in `repo` and return its stripped output."""
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def _has_ref(repo: Path, ref: str) -> bool:
    """Return whether `ref` names a commit in `repo`."""
    done = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def _fetch(repo: Path, remote: str) -> None:
    """Fetch the remote's `pr-assets` into its remote-tracking ref, when the remote has one."""
    if _git(repo, "ls-remote", "--heads", remote, ASSETS_BRANCH):
        refspec = f"+refs/heads/{ASSETS_BRANCH}:refs/remotes/{remote}/{ASSETS_BRANCH}"
        _git(repo, "fetch", "--quiet", remote, refspec)


def _checkout(repo: Path, worktree: Path, remote: str) -> None:
    """Add a worktree of `pr-assets` at `worktree`: the local branch, the remote's, or an orphan.

    Raises:
        ValueError: When the local `pr-assets` has diverged from the remote's.
    """
    local, tracking = f"refs/heads/{ASSETS_BRANCH}", f"refs/remotes/{remote}/{ASSETS_BRANCH}"
    if _has_ref(repo, local) and _has_ref(repo, tracking):
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", local, tracking], cwd=repo, check=False
        )
        if ancestor.returncode == 0:
            _git(repo, "branch", "--force", ASSETS_BRANCH, tracking)
        elif _git(repo, "merge-base", local, tracking) != _git(repo, "rev-parse", tracking):
            raise ValueError(f"local {ASSETS_BRANCH} has diverged from {remote}'s")
    if _has_ref(repo, local):
        _git(repo, "worktree", "add", "--quiet", str(worktree), ASSETS_BRANCH)
    elif _has_ref(repo, tracking):
        _git(repo, "worktree", "add", "--quiet", "-b", ASSETS_BRANCH, str(worktree), tracking)
    else:
        _git(repo, "worktree", "add", "--quiet", "--detach", "--no-checkout", str(worktree))
        _git(worktree, "checkout", "--quiet", "--orphan", ASSETS_BRANCH)
        _git(worktree, "read-tree", "--empty")


def commit_assets(repo: Path, out: Path, pr_branch: str, remote: str, *, push: bool) -> str:
    """Copy `out` to `<pr_branch>/` on `pr-assets`, commit it, push when asked; return the commit.

    Args:
        repo: The repository.
        out: The `diff_images.py` output directory.
        pr_branch: The PR branch the review images belong to.
        remote: The remote fetched from and pushed to.
        push: Whether to push `pr-assets` to `remote`.

    Returns:
        The `pr-assets` commit holding the review images (the existing tip when nothing changed).
    """
    target = assets_dir(pr_branch)
    if push:
        _fetch(repo, remote)
    with tempfile.TemporaryDirectory() as tmp:
        worktree = Path(tmp) / ASSETS_BRANCH
        _checkout(repo, worktree, remote)
        try:
            shutil.rmtree(worktree / target, ignore_errors=True)
            shutil.copytree(out, worktree / target, ignore=shutil.ignore_patterns(PR_BODY))
            _git(worktree, "add", "--all", "--", target)
            if _git(worktree, "status", "--porcelain", "--", target):
                message = f"Diff images for {pr_branch}"
                _git(worktree, "commit", "--quiet", "--no-verify", "-m", message)
            commit = _git(worktree, "rev-parse", "HEAD")
            if push:
                _git(worktree, "push", "--quiet", "--no-verify", remote, ASSETS_BRANCH)
        finally:
            _git(repo, "worktree", "remove", "--force", str(worktree))
    return commit


def pr_body(summary: Summary, slug: str, commit: str, target: str, form: str = "raw") -> str:
    """Return the PR body's Markdown block for review images committed at `commit` under `target`."""
    return markdown(summary, lambda path: asset_url(slug, commit, f"{target}/{path}", form))


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Publish diff images for a PR body.")
    parser.add_argument("out", type=Path, metavar="OUT", help="a diff_images.py output directory")
    parser.add_argument("--pr-branch", default=None, help="the PR branch (default: checked out)")
    parser.add_argument("--remote", default="origin", help="the remote (default: origin)")
    parser.add_argument("--push", action="store_true", help=f"push {ASSETS_BRANCH} to the remote")
    parser.add_argument("--url-form", choices=["raw", "blob"], default="raw", help="link form")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Publish and log the PR body; return 0 when published, 2 when something stops it."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    summary_path = args.out / SUMMARY_JSON
    if not summary_path.is_file():
        logger.error("no %s in %s: run diff_images.py first", SUMMARY_JSON, args.out)
        return 2
    try:
        pr_branch = args.pr_branch or _git(args.repo, "rev-parse", "--abbrev-ref", "HEAD")
        slug = github_slug(_git(args.repo, "remote", "get-url", args.remote))
        commit = commit_assets(args.repo, args.out, pr_branch, args.remote, push=args.push)
    except (ValueError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else exc
        logger.error("not published: %s", detail)  # noqa: TRY400 (the reason is the whole message)
        return 2
    body = pr_body(Summary.from_json(summary_path.read_text()), slug, commit, assets_dir(pr_branch))
    (args.out / PR_BODY).write_text(body)
    logger.info("%s commit %s for %s", ASSETS_BRANCH, commit, pr_branch)
    if not args.push:
        logger.warning("not pushed: the links resolve once %s is pushed", ASSETS_BRANCH)
    logger.info("PR body block (also in %s):\n\n%s", args.out / PR_BODY, body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
