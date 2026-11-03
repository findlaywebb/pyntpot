"""Tests for publishing review images: links, and real commits pushed to a bare `origin` in `tmp_path`."""

import stat
from pathlib import Path

import pytest
from golden.diff_images import SUMMARY_JSON
from golden.diff_report import FileDiff, Summary
from golden.publish_diffs import (
    ASSETS_BRANCH,
    PR_BODY,
    PUSH_ATTEMPTS,
    PublishError,
    asset_url,
    assets_dir,
    commit_assets,
    github_slug,
    main,
)

from support.git_commands import git, is_commit
from support.git_repos import bare_remote, commit_all, scratch_repo

COMMIT = "0123456789abcdef0123456789abcdef01234567"
GITHUB_URL = "https://github.com/findlaywebb/pyntpot"
REMOTE_HEAD = f"refs/heads/{ASSETS_BRANCH}"

#: A pre-receive hook standing in for another publisher: it moves `pr-assets` on by one
#: commit, then refuses this push, as a race lost to a push that landed first would. With
#: `RACES` in the repository it races only that many times; without it, every time.
_RACING_HOOK = """#!/bin/sh
count=$(cat "$GIT_DIR/raced" 2>/dev/null || echo 0)
if [ -f "$GIT_DIR/RACES" ] && [ "$count" -ge "$(cat "$GIT_DIR/RACES")" ]; then exit 0; fi
echo $((count + 1)) > "$GIT_DIR/raced"
unset GIT_QUARANTINE_PATH GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
export GIT_AUTHOR_NAME=Other GIT_AUTHOR_EMAIL=other@example.invalid
export GIT_COMMITTER_NAME=Other GIT_COMMITTER_EMAIL=other@example.invalid
tip=$(git rev-parse refs/heads/pr-assets)
next=$(git commit-tree -p "$tip" -m "Another publish" "$tip^{tree}")
git update-ref refs/heads/pr-assets "$next" "$tip"
echo "racing publisher moved pr-assets" >&2
exit 1
"""


class TestLinks:
    """Links name the repository from its remote, and the `pr-assets` commit."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/findlaywebb/pyntpot",
            "https://github.com/findlaywebb/pyntpot.git",
            "git@github.com:findlaywebb/pyntpot.git",
            "ssh://git@github.com/findlaywebb/pyntpot/",
        ],
        ids=["https", "https-git", "scp-ssh", "ssh-url"],
    )
    def test_the_slug_comes_from_any_github_remote_form(self, url: str) -> None:
        """HTTPS and SSH remotes, with or without `.git`, name the same repository."""
        assert github_slug(url) == "findlaywebb/pyntpot"

    def test_a_remote_elsewhere_is_refused(self) -> None:
        """A remote that is not GitHub has no raw-file host to link."""
        with pytest.raises(ValueError, match="not a GitHub remote"):
            github_slug("https://example.invalid/pyntpot.git")

    def test_a_raw_link_quotes_each_segment(self) -> None:
        """A raw link names the commit and quotes spaces, keeping slashes."""
        path = "fix/a b/docs/images/hero.webp.diff.png"
        assert asset_url("o/r", COMMIT, path) == (
            f"https://raw.githubusercontent.com/o/r/{COMMIT}/fix/a%20b/docs/images/hero.webp.diff.png"
        )

    @pytest.mark.parametrize(
        "name",
        ["", "/abs", "a/../b", "./a", "HEAD"],
        ids=["empty", "absolute", "up", "dot", "detached"],
    )
    def test_a_branch_name_that_climbs_is_refused(self, name: str) -> None:
        """A PR branch name never places review images outside its own directory."""
        with pytest.raises(ValueError, match="unusable"):
            assets_dir(name)

    def test_a_slashed_branch_name_nests(self) -> None:
        """`fix/53-river` keeps its slash as a directory."""
        assert assets_dir("fix/53-river") == "fix/53-river"


def _diff_output(root: Path, drawn: bytes = b"diff image one", name: str = "hero.webp") -> Path:
    """Write a minimal `diff_images.py` output: one review image and the summary naming it."""
    (root / "docs/images").mkdir(parents=True)
    (root / f"docs/images/{name}.diff.png").write_bytes(drawn)
    summary = Summary(
        "origin/main",
        "working tree",
        (FileDiff(f"docs/images/{name}", "changed", None, f"docs/images/{name}.diff.png"),),
    )
    (root / SUMMARY_JSON).write_text(summary.to_json())
    return root


def _origin_tip(origin: Path) -> str:
    """Return the bare remote's `pr-assets` commit."""
    return git(origin, "rev-parse", REMOTE_HEAD)


def _files(repo: Path, commit: str) -> list[str]:
    """Return every file path in a commit's tree."""
    return git(repo, "ls-tree", "-r", "--name-only", commit).splitlines()


def _push_from_another_clone(origin: Path, root: Path) -> str:
    """Push one more `pr-assets` commit to `origin` from a separate repository; return it."""
    other = scratch_repo(root)
    git(other, "fetch", "--quiet", str(origin), REMOTE_HEAD)
    git(other, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    (other / "fix/99").mkdir(parents=True)
    (other / "fix/99/summary.json").write_text("{}\n")
    theirs = commit_all(other, "Review images for fix/99")
    git(other, "push", "--quiet", str(origin), f"HEAD:{REMOTE_HEAD}")
    return theirs


def _racing(origin: Path, races: int | None) -> None:
    """Install the racing publisher on `origin`, racing `races` times, or every time when `None`."""
    hooks = origin / "hooks"
    hook = hooks / "pre-receive"
    hook.write_text(_RACING_HOOK)
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    git(origin, "config", "core.hooksPath", str(hooks))
    if races is not None:
        (origin / "RACES").write_text(f"{races}\n")


class TestPublish:
    """The commit is built on `origin`'s tip in a temporary worktree and pushed as a fast-forward."""

    @pytest.fixture
    def origin(self, tmp_path: Path) -> Path:
        """Return a bare repository standing in for `origin`, refusing non-fast-forward pushes."""
        return bare_remote(tmp_path / "origin.git")

    @pytest.fixture
    def repo(self, tmp_path: Path, origin: Path) -> Path:
        """Return a clone-like repository: one commit on `main`, `origin` set, an uncommitted edit.

        `origin`'s URL is the GitHub one the links are made from; git rewrites it to the bare
        repository for every fetch and push.
        """
        repo = scratch_repo(tmp_path / "repo")
        (repo / "code.py").write_text("x = 1\n")
        commit_all(repo, "first")
        git(repo, "remote", "add", "origin", GITHUB_URL)
        git(repo, "config", f"url.{origin}.insteadOf", GITHUB_URL)
        (repo / "code.py").write_text("x = 2\n")
        git(repo, "add", "code.py")
        (repo / "code.py").write_text("x = 3\n")
        return repo

    def _publish(self, repo: Path, out: Path, branch: str = "fix/53", **options) -> str:
        """Publish `out` for `branch`, pushing."""
        return commit_assets(repo, out, branch, "origin", push=True, **options)

    def test_the_first_publish_creates_the_branch_as_an_orphan(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """`origin` gains `pr-assets`: one parentless commit holding only the PR's directory."""
        commit = self._publish(repo, _diff_output(tmp_path / "out"))
        assert _origin_tip(origin) == commit
        assert git(origin, "rev-list", "--count", commit) == "1"
        assert _files(origin, commit) == [
            "fix/53/docs/images/hero.webp.diff.png",
            f"fix/53/{SUMMARY_JSON}",
        ]

    def test_a_second_publish_fast_forwards_and_keeps_other_prs(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """Each push's parent is the remote's earlier tip; another PR's files stay beside it."""
        first = self._publish(repo, _diff_output(tmp_path / "a"))
        second = self._publish(repo, _diff_output(tmp_path / "b"), "tooling/x")
        again = self._publish(repo, _diff_output(tmp_path / "c", b"two", "other.webp"))
        assert git(origin, "rev-list", "--first-parent", REMOTE_HEAD).splitlines() == [
            again,
            second,
            first,
        ]
        files = _files(origin, again)
        assert "fix/53/docs/images/hero.webp.diff.png" not in files
        assert "fix/53/docs/images/other.webp.diff.png" in files
        assert "tooling/x/docs/images/hero.webp.diff.png" in files

    def test_a_publish_builds_on_a_tip_someone_else_pushed(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """A tip pushed from another clone is fetched and built on, never overwritten."""
        self._publish(repo, _diff_output(tmp_path / "a"))
        theirs = _push_from_another_clone(origin, tmp_path / "other")
        ours = self._publish(repo, _diff_output(tmp_path / "b", b"two"))
        assert git(origin, "rev-parse", f"{ours}^") == theirs
        assert "fix/99/summary.json" in _files(origin, ours)

    def test_an_unchanged_republish_pushes_nothing(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """Publishing the same review images again returns the remote's tip and adds no commit."""
        first = self._publish(repo, _diff_output(tmp_path / "a"))
        assert self._publish(repo, _diff_output(tmp_path / "b")) == first
        assert _origin_tip(origin) == first

    def test_the_users_head_index_tree_and_branches_are_untouched(
        self, repo: Path, tmp_path: Path
    ) -> None:
        """HEAD, the staged and unstaged edits and the branch list stay; no worktree is left."""
        head, branches = git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--list")
        status = git(repo, "status", "--porcelain")
        self._publish(repo, _diff_output(tmp_path / "a"))
        self._publish(repo, _diff_output(tmp_path / "b", b"two"))
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
        assert git(repo, "rev-parse", "HEAD") == head
        assert git(repo, "status", "--porcelain") == status == "MM code.py"
        assert git(repo, "branch", "--list") == branches
        assert not is_commit(repo, f"refs/heads/{ASSETS_BRANCH}")
        assert len(git(repo, "worktree", "list").splitlines()) == 1

    def test_a_dry_run_pushes_nothing_and_leaves_no_branch(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """Without push the commit is built on the remote tip, but `origin` and the branches stay."""
        first = self._publish(repo, _diff_output(tmp_path / "a"))
        dry = commit_assets(
            repo, _diff_output(tmp_path / "b", b"two"), "fix/53", "origin", push=False
        )
        assert git(repo, "rev-parse", f"{dry}^") == first
        assert _origin_tip(origin) == first
        assert not is_commit(repo, f"refs/heads/{ASSETS_BRANCH}")

    def test_a_dry_run_never_blocks_a_later_publish(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """After a dry run and someone else's push, a publish still lands on their tip."""
        self._publish(repo, _diff_output(tmp_path / "a"))
        commit_assets(repo, _diff_output(tmp_path / "b", b"two"), "fix/53", "origin", push=False)
        theirs = _push_from_another_clone(origin, tmp_path / "other")
        ours = self._publish(repo, _diff_output(tmp_path / "c", b"three"))
        assert git(origin, "rev-parse", f"{ours}^") == theirs
        assert _origin_tip(origin) == ours

    def test_a_push_that_loses_a_race_is_rebuilt_on_the_new_tip(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """A push refused because the tip moved is fetched again, rebuilt on it and pushed."""
        first = self._publish(repo, _diff_output(tmp_path / "a"))
        _racing(origin, races=1)
        ours = self._publish(repo, _diff_output(tmp_path / "b", b"two"))
        raced = git(origin, "rev-parse", f"{ours}^")
        assert git(origin, "log", "-1", "--format=%s", raced) == "Another publish"
        assert git(origin, "rev-parse", f"{raced}^") == first
        assert _origin_tip(origin) == ours

    def test_a_remote_that_keeps_moving_stops_the_publish(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """After `PUSH_ATTEMPTS` lost races the publish fails, naming the count, and pushes nothing."""
        self._publish(repo, _diff_output(tmp_path / "a"))
        _racing(origin, races=None)
        with pytest.raises(PublishError, match=f"before each of {PUSH_ATTEMPTS} pushes"):
            self._publish(repo, _diff_output(tmp_path / "b", b"two"))
        assert (origin / "raced").read_text().strip() == str(PUSH_ATTEMPTS)
        assert git(origin, "log", "-1", "--format=%s", REMOTE_HEAD) == "Another publish"
        assert len(git(repo, "worktree", "list").splitlines()) == 1

    def test_a_refused_push_with_an_unmoved_tip_fails_at_once(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """A remote that refuses outright is not retried: the error carries git's reason."""
        self._publish(repo, _diff_output(tmp_path / "a"))
        hook = origin / "hooks/pre-receive"
        hook.write_text('#!/bin/sh\necho "pushes are closed" >&2\nexit 1\n')
        hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
        git(origin, "config", "core.hooksPath", str(origin / "hooks"))
        with pytest.raises(PublishError, match="pushes are closed"):
            self._publish(repo, _diff_output(tmp_path / "b", b"two"))

    def test_an_excludes_file_ignoring_pngs_drops_no_review_image(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """A user's excludes file ignoring `*.png` (as a global one would) still publishes the PNG."""
        excludes = tmp_path / "excludes"
        excludes.write_text("*.png\n")
        git(repo, "config", "core.excludesFile", str(excludes))
        commit = self._publish(repo, _diff_output(tmp_path / "out"))
        assert "fix/53/docs/images/hero.webp.diff.png" in _files(origin, commit)

    def test_a_failed_build_removes_its_worktree_and_keeps_the_error(
        self, repo: Path, tmp_path: Path
    ) -> None:
        """An `OUT` that is not a directory fails the copy; that error surfaces, no worktree is left."""
        missing = tmp_path / "missing"
        with pytest.raises(FileNotFoundError):
            self._publish(repo, missing)
        assert len(git(repo, "worktree", "list").splitlines()) == 1

    def test_main_pushes_and_writes_the_pr_body_with_commit_links(
        self, repo: Path, origin: Path, tmp_path: Path
    ) -> None:
        """The command names the current branch's directory and links raw files at the pushed commit."""
        out = _diff_output(tmp_path / "out")
        assert main([str(out), "--repo", str(repo), "--push"]) == 0
        commit = _origin_tip(origin)
        body = (out / PR_BODY).read_text()
        want = f"https://raw.githubusercontent.com/findlaywebb/pyntpot/{commit}/main/docs/images/hero.webp.diff.png"
        assert f"]({want})" in body
        assert PR_BODY not in "\n".join(_files(origin, commit))

    def test_main_says_a_dry_runs_links_are_not_live(
        self, repo: Path, origin: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Without `--push` the block is written, the remote gains nothing, and the log says so."""
        out = _diff_output(tmp_path / "out")
        assert main([str(out), "--repo", str(repo)]) == 0
        assert (out / PR_BODY).is_file()
        assert git(origin, "for-each-ref") == ""
        assert "not live yet" in caplog.text

    def test_main_needs_a_summary(self, repo: Path, tmp_path: Path) -> None:
        """A directory that is not a diff output is refused before git is touched."""
        (tmp_path / "empty").mkdir()
        assert main([str(tmp_path / "empty"), "--repo", str(repo)]) == 2
        assert git(repo, "for-each-ref", f"refs/remotes/origin/{ASSETS_BRANCH}") == ""
