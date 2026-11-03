"""Tests for publishing diff images: links, and a real commit to `pr-assets` in a scratch repository."""

from pathlib import Path

import pytest
from golden.diff_images import SUMMARY_JSON
from golden.diff_report import FileDiff, Summary
from golden.publish_diffs import (
    ASSETS_BRANCH,
    PR_BODY,
    asset_url,
    assets_dir,
    commit_assets,
    github_slug,
    main,
)

from support.git_repos import commit_all, git, scratch_repo

COMMIT = "0123456789abcdef0123456789abcdef01234567"


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

    def test_raw_and_blob_links_quote_each_segment(self) -> None:
        """A raw link and a blob link name the commit and quote spaces, keeping slashes."""
        path = "fix/a b/docs/images/hero.webp.diff.png"
        assert asset_url("o/r", COMMIT, path) == (
            f"https://raw.githubusercontent.com/o/r/{COMMIT}/fix/a%20b/docs/images/hero.webp.diff.png"
        )
        assert asset_url("o/r", COMMIT, path, "blob") == (
            f"https://github.com/o/r/blob/{COMMIT}/fix/a%20b/docs/images/hero.webp.diff.png?raw=true"
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


def _diff_output(root: Path, drawn: bytes = b"diff image one") -> Path:
    """Write a minimal `diff_images.py` output: one review image and the summary naming it."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "docs/images").mkdir(parents=True)
    (root / "docs/images/hero.webp.diff.png").write_bytes(drawn)
    summary = Summary(
        "origin/main",
        "working tree",
        (FileDiff("docs/images/hero.webp", "changed", None, "docs/images/hero.webp.diff.png"),),
    )
    (root / SUMMARY_JSON).write_text(summary.to_json())
    return root


class TestCommit:
    """The review images are committed to `pr-assets` without touching the checked-out branch."""

    @pytest.fixture
    def repo(self, tmp_path: Path) -> Path:
        """Return a repository with one commit on `main`, a GitHub remote and an uncommitted edit."""
        repo = scratch_repo(tmp_path / "repo")
        (repo / "code.py").write_text("x = 1\n")
        commit_all(repo, "first")
        git(repo, "remote", "add", "origin", "https://github.com/findlaywebb/pyntpot")
        (repo / "code.py").write_text("x = 2\n")
        return repo

    def test_the_first_publish_makes_an_orphan_holding_only_the_review_images(
        self, repo: Path, tmp_path: Path
    ) -> None:
        """`pr-assets` starts with no parent and no file but the PR's directory."""
        commit = commit_assets(repo, _diff_output(tmp_path / "out"), "fix/53", "origin", push=False)
        assert git(repo, "rev-parse", ASSETS_BRANCH) == commit
        assert git(repo, "rev-list", "--count", commit) == "1"
        assert git(repo, "ls-tree", "-r", "--name-only", commit).splitlines() == [
            "fix/53/docs/images/hero.webp.diff.png",
            f"fix/53/{SUMMARY_JSON}",
        ]

    def test_the_working_branch_index_and_tree_are_untouched(
        self, repo: Path, tmp_path: Path
    ) -> None:
        """HEAD stays on `main` at its commit, the edit stays unstaged, and no worktree is left."""
        head = git(repo, "rev-parse", "HEAD")
        commit_assets(repo, _diff_output(tmp_path / "out"), "fix/53", "origin", push=False)
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
        assert git(repo, "rev-parse", "HEAD") == head
        assert git(repo, "status", "--porcelain") == "M code.py"
        assert len(git(repo, "worktree", "list").splitlines()) == 1

    def test_a_republish_replaces_the_prs_directory_and_keeps_others(
        self, repo: Path, tmp_path: Path
    ) -> None:
        """A second PR's review images sit beside the first's; republishing the first replaces only its files."""
        first = commit_assets(repo, _diff_output(tmp_path / "a"), "fix/53", "origin", push=False)
        commit_assets(repo, _diff_output(tmp_path / "b"), "tooling/x", "origin", push=False)
        again = _diff_output(tmp_path / "c", b"diff image two")
        (again / "docs/images/hero.webp.diff.png").rename(again / "docs/images/other.diff.png")
        last = commit_assets(repo, again, "fix/53", "origin", push=False)
        files = git(repo, "ls-tree", "-r", "--name-only", last).splitlines()
        assert "fix/53/docs/images/hero.webp.diff.png" not in files
        assert "fix/53/docs/images/other.diff.png" in files
        assert "tooling/x/docs/images/hero.webp.diff.png" in files
        assert git(repo, "merge-base", "--is-ancestor", first, last) == ""

    def test_an_unchanged_republish_makes_no_commit(self, repo: Path, tmp_path: Path) -> None:
        """Publishing the same review images again returns the existing tip."""
        first = commit_assets(repo, _diff_output(tmp_path / "a"), "fix/53", "origin", push=False)
        assert (
            commit_assets(repo, _diff_output(tmp_path / "b"), "fix/53", "origin", push=False)
            == first
        )

    def test_main_writes_the_pr_body_with_commit_links(self, repo: Path, tmp_path: Path) -> None:
        """The command names the current branch's directory and links raw files at the new commit."""
        out = _diff_output(tmp_path / "out")
        assert main([str(out), "--repo", str(repo)]) == 0
        commit = git(repo, "rev-parse", ASSETS_BRANCH)
        body = (out / PR_BODY).read_text()
        want = f"https://raw.githubusercontent.com/findlaywebb/pyntpot/{commit}/main/docs/images/hero.webp.diff.png"
        assert f"]({want})" in body
        assert PR_BODY not in git(repo, "ls-tree", "-r", "--name-only", commit)

    def test_main_needs_a_summary(self, repo: Path, tmp_path: Path) -> None:
        """A directory that is not a diff output is refused before git is touched."""
        (tmp_path / "empty").mkdir()
        assert main([str(tmp_path / "empty"), "--repo", str(repo)]) == 2
        assert git(repo, "branch", "--list", ASSETS_BRANCH) == ""
