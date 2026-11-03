r"""The docs site's pages, nav and Markdown pieces, read the way the docs-truth checks need.

The one reader of the site's shape for `tests/docs/`. Pages come from `mkdocs.yml`
(`docs_dir` minus `exclude_docs`), reading order from its nav, and each page's fenced
blocks, prose and links from its Markdown text. `resolve_dotted` is the one resolver of a
dotted `pyntpot.…` path to the object it names.

Key names:

- `MKDOCS`, `DOCS`: the site configuration and the docs directory.
- `excluded`, `site_pages`: the `exclude_docs` entries, and the pages they leave.
- `NavEntry`, `nav`: the nav's page entries, each with the sections it sits in.
- `Block`, `fenced_blocks`, `prose`: fenced code blocks, and the text without them.
- `links`, `resolve`: link targets in page order, and the file a relative one names.
- `resolve_dotted`: a dotted path's object, module first.

Every helper but `site_pages` and `resolve_dotted` is a pure function of its text
arguments. It does not build the site, parse YAML (PyYAML is not a declared dependency, so
`nav` and `excluded` read the few shapes `mkdocs.yml` uses by indentation), render
Markdown, or read reference-style links. Exclusion entries follow gitignore's rules for
plain names: an entry with no inner `/` matches at any depth, one ending in `/` matches
only a directory. `nav` reads everything after the first `"\nnav:\n"`, so `nav:` must be
the file's last top-level key.
"""

import importlib
import re
from dataclasses import dataclass
from pathlib import Path

from support import REPO_ROOT

#: The site configuration.
MKDOCS: Path = REPO_ROOT / "mkdocs.yml"

#: The docs directory, `docs_dir` in `MKDOCS`.
DOCS: Path = REPO_ROOT / "docs"

_NAV_LINE = re.compile(r"^(?P<indent>\s*)- (?:(?P<title>[^:]+):)?\s*(?P<path>\S.*?)?\s*$")
_FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?(?P<href>[^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_COMMENT = re.compile(r"^<!--.*-->$")


@dataclass(frozen=True)
class NavEntry:
    """One page in the nav: its path under `docs/` and the titles of the sections it sits in, outermost first."""

    path: str
    sections: tuple[str, ...]


@dataclass(frozen=True)
class Block:
    """One fenced code block.

    `lang` is the info string's first word (empty when there is none), `code` the lines
    between the fences dedented by the opening fence's indent, `marker` the nearest
    preceding non-blank line when it is an HTML comment, and `line` the 1-based line of
    the opening fence.
    """

    lang: str
    code: str
    marker: str | None
    line: int


def excluded(text: str) -> tuple[str, ...]:
    """Return the entries of `text`'s `exclude_docs: |` block, in file order."""
    lines = text.splitlines()
    try:
        start = lines.index("exclude_docs: |") + 1
    except ValueError:
        return ()
    entries: list[str] = []
    for line in lines[start:]:
        if line.strip() and not line[0].isspace():
            break
        if line.strip():
            entries.append(line.strip())
    return tuple(entries)


def _is_excluded(relative: Path, entry: str) -> bool:
    """Return whether a page path under `docs/` matches one plain gitignore-style entry."""
    directory = entry.endswith("/")
    pattern = entry.strip("/").split("/")
    parts = relative.parts
    # A directory entry can match only a parent, never the page's own file name.
    candidates = parts[:-1] if directory else parts
    if len(pattern) > 1 or entry.startswith("/"):
        return tuple(candidates[: len(pattern)]) == tuple(pattern)
    return pattern[0] in candidates


def site_pages() -> list[Path]:
    """Return every Markdown page the site builds from `docs/`, sorted."""
    entries = excluded(MKDOCS.read_text())
    return sorted(
        page
        for page in DOCS.rglob("*.md")
        if not any(_is_excluded(page.relative_to(DOCS), entry) for entry in entries)
    )


def nav(text: str) -> list[NavEntry]:
    """Return the page entries of `text`'s nav, in nav order, each with its section titles."""
    _, _, body = text.partition("\nnav:\n")
    stack: list[tuple[int, str]] = []
    entries: list[NavEntry] = []
    for line in body.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        found = _NAV_LINE.match(line)
        if found is None:
            if not line[0].isspace():
                break
            continue
        indent = len(found["indent"])
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if found["path"] is None:
            stack.append((indent, (found["title"] or "").strip()))
        else:
            entries.append(NavEntry(found["path"], tuple(title for _, title in stack)))
    return entries


def _scan(text: str) -> tuple[list[Block], list[str]]:
    """Return a page's fenced blocks and its lines outside them."""
    lines = text.splitlines()
    blocks: list[Block] = []
    outside: list[str] = []
    index = 0
    while index < len(lines):
        opening = _FENCE_OPEN.match(lines[index])
        if opening is None or (opening["fence"][0] == "`" and "`" in opening["info"]):
            outside.append(lines[index])
            index += 1
            continue
        indent, fence = opening["indent"], opening["fence"]
        closing = re.compile(rf"^[ \t]*{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")
        end = index + 1
        while end < len(lines) and not closing.match(lines[end]):
            end += 1
        code = [_dedent(line, len(indent)) for line in lines[index + 1 : end]]
        above = next((line.strip() for line in reversed(outside) if line.strip()), "")
        info = opening["info"].split()
        blocks.append(
            Block(
                lang=info[0] if info else "",
                code="\n".join(code),
                marker=above if _COMMENT.match(above) else None,
                line=index + 1,
            )
        )
        index = end + 1
    return blocks, outside


def _dedent(line: str, width: int) -> str:
    """Return `line` with up to `width` leading spaces removed, and no more."""
    leading = len(line) - len(line.lstrip(" "))
    return line[min(leading, width) :]


def fenced_blocks(text: str) -> list[Block]:
    """Return every fenced code block in `text`, backtick or tilde, at the margin or indented, in page order."""
    return _scan(text)[0]


def prose(text: str) -> str:
    """Return `text` with every fenced block, fences included, removed."""
    return "\n".join(_scan(text)[1])


def links(text: str) -> list[str]:
    """Return the targets of `text`'s inline Markdown links outside code blocks, images excluded, in page order."""
    return [found["href"] for found in _LINK.finditer(prose(text))]


def resolve(page: Path, href: str) -> Path | None:
    """Return the file a relative link on `page` names, fragment dropped; `None` for an absolute URL or path."""
    if _SCHEME.match(href) or href.startswith("/"):
        return None
    target = href.split("#", maxsplit=1)[0]
    if not target:
        return page.resolve()
    return (page.parent / target).resolve()


def resolve_dotted(path: str) -> object:
    """Return the object a dotted path names.

    Imports the longest importable module prefix, then reads each remaining part as an
    attribute. Module first is deliberate: where a module shadows a package attribute of
    the same name, the path resolves to the module.

    Raises:
        LookupError: when no prefix imports or a remaining part is missing; names `path`.
    """
    parts = path.split(".")
    for cut in range(len(parts), 0, -1):
        module_name = ".".join(parts[:cut])
        try:
            found: object = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name is not None and f"{module_name}.".startswith(f"{exc.name}."):
                continue
            raise
        for part in parts[cut:]:
            try:
                found = getattr(found, part)
            except AttributeError as exc:
                raise LookupError(f"{path}: {part!r} is not an attribute") from exc
        return found
    raise LookupError(f"{path}: no prefix of it is an importable module")
