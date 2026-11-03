"""Every tutorial page's quoted code is the script's own text.

A fenced block whose marker (the nearest non-blank line above its fence) is
`<!-- from examples/<path> -->` is a verbatim substring of that file, on every page under
`docs/tutorials/`, and every `python` block on those pages carries such a marker. A new
tutorial page is covered with no test edit. This does not run the scripts or check prose.
"""

import re
from pathlib import Path

import pytest

from support.examples import EXAMPLES_DIR
from support.site_pages import DOCS, fenced_blocks

_TUTORIALS = DOCS / "tutorials"
_PAGES: list[Path] = sorted(_TUTORIALS.rglob("*.md"))
_IDS: list[str] = [page.relative_to(_TUTORIALS).as_posix() for page in _PAGES]
_FROM_EXAMPLES = re.compile(r"^<!--\s*from examples/(?P<path>\S+)\s*-->$")


@pytest.mark.parametrize("page", _PAGES, ids=_IDS)
def test_every_marked_block_on_every_tutorial_page_is_verbatim(page: Path) -> None:
    """Each block under a `from examples/...` marker appears unchanged in the file it names."""
    drifted: list[str] = []
    for block in fenced_blocks(page.read_text()):
        found = _FROM_EXAMPLES.match(block.marker or "")
        if found is None:
            continue
        source = EXAMPLES_DIR / found["path"]
        if not source.is_file() or block.code not in source.read_text():
            drifted.append(f"line {block.line}: examples/{found['path']}")
    assert not drifted, f"quoted code that is not in its file: {drifted}"


@pytest.mark.parametrize("page", _PAGES, ids=_IDS)
def test_every_python_block_on_a_tutorial_page_is_marked(page: Path) -> None:
    """Each fenced `python` block on a tutorial page carries a `from examples/` marker."""
    unmarked = [
        block.line
        for block in fenced_blocks(page.read_text())
        if block.lang == "python" and _FROM_EXAMPLES.match(block.marker or "") is None
    ]
    assert not unmarked, f"python blocks with no `from examples/` marker, at lines {unmarked}"
