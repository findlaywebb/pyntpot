"""Every image the README and docs/ show is registered, within budget, and linked by a stable URL.

`support.docs_images.IMAGES` is the registry. This checks it against the files under
`docs/images/` and against the Markdown that shows them: every file is registered and every
entry has its file; every image a Markdown file shows is registered; each file is within its
kind's budget, each slice within its share, the directory within its total; and the README
links nothing by a relative path. A link or image into this repo from the README is an
absolute URL on `raw.githubusercontent.com/findlaywebb/pyntpot/` or
`github.com/findlaywebb/pyntpot/` at `main` or a `v*` tag; badges and links to other sites
are allowed. Code spans and fenced blocks are not read.
"""

import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from support import REPO_ROOT
from support.docs_images import (
    IMAGES,
    IMAGES_DIR,
    KIND_BUDGET_BYTES,
    SLICE_SHARE_BYTES,
    TOTAL_BUDGET_BYTES,
)

_IMAGES_ROOT = REPO_ROOT / IMAGES_DIR
_REPO = "findlaywebb/pyntpot"
_RAW_PREFIX = f"/{_REPO}/"
_REF = re.compile(r"main|v\d[^/]*")
_FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.DOTALL | re.MULTILINE)
_CODE_SPAN = re.compile(r"`[^`\n]*`")
_TARGET = re.compile(r"\]\(\s*<?([^)\s>]+)")
_IMG_MD = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)")
_IMG_HTML = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
_EXTENSIONS = {"webp-lossless": ".webp", "webp-lossy": ".webp", "jpeg": ".jpg"}


def _markdown_files() -> list[Path]:
    """Return the README and every Markdown file under docs/ that is not a decision record."""
    docs = [p for p in (REPO_ROOT / "docs").rglob("*.md") if "decisions" not in p.parts]
    return [REPO_ROOT / "README.md", *sorted(docs)]


def _prose(path: Path) -> str:
    """Return a Markdown file's text without fenced blocks and code spans."""
    return _CODE_SPAN.sub("", _FENCE.sub("", path.read_text()))


def _repo_path(target: str) -> tuple[str, str] | None:
    """Return the ref and repo path an absolute URL into this repo's tree names, else `None`."""
    parts = urlsplit(target)
    if parts.hostname == "raw.githubusercontent.com" and parts.path.startswith(_RAW_PREFIX):
        ref, _, rest = parts.path.removeprefix(_RAW_PREFIX).partition("/")
        return ref, rest
    if parts.hostname == "github.com" and parts.path.startswith(_RAW_PREFIX):
        kind, _, tail = parts.path.removeprefix(_RAW_PREFIX).partition("/")
        if kind in {"blob", "tree", "raw"}:
            ref, _, rest = tail.partition("/")
            return ref, rest
    return None


def _shown_path(source: Path, target: str) -> str | None:
    """Return the repo path an image target shows, or `None` when it is on another site."""
    if target.startswith(("http://", "https://")):
        found = _repo_path(target)
        return None if found is None else found[1]
    relative = PurePosixPath(urlsplit(target).path)
    return str(PurePosixPath(source.parent.relative_to(REPO_ROOT).as_posix()) / relative)


def _normalised(path: str) -> str:
    """Return a repo path with its `.` and `..` parts resolved."""
    out: list[str] = []
    for part in PurePosixPath(path).parts:
        if part == "..":
            if out:
                out.pop()
        elif part != ".":
            out.append(part)
    return "/".join(out)


def _files() -> set[str]:
    """Return every file under docs/images/ as a path relative to it."""
    return {p.relative_to(_IMAGES_ROOT).as_posix() for p in _IMAGES_ROOT.rglob("*") if p.is_file()}


def _size(image: str) -> int:
    """Return a registered file's size in bytes."""
    return (_IMAGES_ROOT / image).stat().st_size


def test_every_file_is_registered_and_every_entry_has_its_file() -> None:
    """The files under docs/images/ and the registered paths are the same set, and no path repeats."""
    registered = [entry.image for entry in IMAGES]
    assert len(registered) == len(set(registered)), "an image is registered twice"
    assert _files() == set(registered)


def test_each_entry_names_a_known_slice_and_an_extension_its_encoding_writes() -> None:
    """Each entry's slice has a share, its kind a budget, its script exists and its extension fits."""
    for entry in IMAGES:
        assert entry.slice in SLICE_SHARE_BYTES, f"{entry.image}: no share for {entry.slice}"
        assert entry.kind in KIND_BUDGET_BYTES, f"{entry.image}: no budget for {entry.kind}"
        assert (REPO_ROOT / "examples" / f"{entry.stem}.py").is_file(), f"{entry.image}: no script"
        assert entry.image.endswith(_EXTENSIONS[entry.encoding]), f"{entry.image}: extension"
        if entry.fixture is not None:
            assert (REPO_ROOT / "tests" / "fixtures" / entry.fixture).is_dir(), entry.image


def test_every_image_a_markdown_file_shows_is_registered() -> None:
    """Each image the README or a docs page shows from this repo is a registered docs image."""
    registered = {f"{IMAGES_DIR}/{entry.image}" for entry in IMAGES}
    unregistered: list[str] = []
    for path in _markdown_files():
        text = _prose(path)
        for target in [*_IMG_MD.findall(text), *_IMG_HTML.findall(text)]:
            shown = _shown_path(path, target)
            if shown is not None and _normalised(shown) not in registered:
                unregistered.append(f"{path.relative_to(REPO_ROOT)}: {target}")
    assert not unregistered, f"images that are not registered: {unregistered}"


def test_each_file_is_within_its_kinds_budget() -> None:
    """No image weighs more than its kind allows."""
    over = [
        f"{entry.image}: {_size(entry.image)} over {KIND_BUDGET_BYTES[entry.kind]}"
        for entry in IMAGES
        if _size(entry.image) > KIND_BUDGET_BYTES[entry.kind]
    ]
    assert not over, f"images over budget: {over}"


def test_each_slice_is_within_its_share_and_the_directory_within_its_total() -> None:
    """A slice's images add up to at most its share, and all images to at most the total."""
    used: dict[str, int] = defaultdict(int)
    for entry in IMAGES:
        used[entry.slice] += _size(entry.image)
    over = [
        f"{name}: {size} over {SLICE_SHARE_BYTES[name]}"
        for name, size in used.items()
        if size > SLICE_SHARE_BYTES[name]
    ]
    assert not over, f"slices over their share: {over}"
    assert sum(used.values()) <= TOTAL_BUDGET_BYTES


def test_the_readme_links_only_by_stable_absolute_urls() -> None:
    """No README link or image is relative, and one into this repo is on main or a v* tag."""
    text = _prose(REPO_ROOT / "README.md")
    targets = [*_TARGET.findall(text), *_IMG_HTML.findall(text)]
    relative = [t for t in targets if not t.startswith(("http://", "https://", "mailto:", "#"))]
    assert not relative, f"relative README targets: {relative}"
    unstable = [
        t for t in targets if (found := _repo_path(t)) is not None and not _REF.fullmatch(found[0])
    ]
    assert not unstable, f"README targets not at main or a v* tag: {unstable}"
