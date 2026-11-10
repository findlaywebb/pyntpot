"""Every theme and palette YAML block on the theme how-to and the line effects how-to loads, or fails, as the page says.

A block is a theme file by default, saved as `my-theme.yaml`. A comment line above the fence
names it: `<!-- theme: NAME -->` saves a theme as `NAME`, `<!-- theme: NAME broken -->` says
loading it raises `ThemeError` and that the page prints each of its messages, and
`<!-- palette: NAME -->` saves a palette file that `Palette.from_file` reads. Blocks are saved
in page order into one directory, so a later block can `extends` an earlier one by name. It
does not render the page or check prose.
"""

import re
import shutil
from pathlib import Path

from pyntpot.maps import Palette, Style, ThemeError

from support.site_pages import DOCS, fenced_blocks

EXAMPLE_THEMES = DOCS.parent / "examples" / "themes"

_PAGES = (
    DOCS / "how-to" / "write-a-theme.md",
    DOCS / "how-to" / "case-light-or-shadow-a-line.md",
)
_MARKER = re.compile(r"<!-- (?P<kind>theme|palette): (?P<name>\S+)(?P<broken> broken)? -->")


def test_every_yaml_block_loads_or_fails_as_marked(tmp_path: Path) -> None:
    """Each yaml block loads through the theme checker, or raises `ThemeError` with messages the page prints."""
    loaded = 0
    for page in _PAGES:
        loaded += _check_page(page, tmp_path / page.stem)
    assert loaded >= 14


def _check_page(page: Path, directory: Path) -> int:
    """Load or fail each yaml block of `page` saved in `directory`, beside the example themes; return how many loaded."""
    text = page.read_text()
    shutil.copytree(EXAMPLE_THEMES, directory)
    loaded = 0
    for block in fenced_blocks(text):
        if block.lang != "yaml":
            continue
        found = _MARKER.fullmatch(block.marker or "")
        kind, name, broken = (
            (found["kind"], found["name"], bool(found["broken"]))
            if found
            else ("theme", "my-theme.yaml", False)
        )
        if all(line.startswith("#") for line in block.code.splitlines()):
            continue
        path = directory / name
        path.write_text(block.code, encoding="utf-8")
        if kind == "palette":
            Palette.from_file(path)
        elif broken:
            try:
                Style.from_theme(path)
            except ThemeError as error:
                for problem in error.problems:
                    assert problem.message in text, (block.line, problem.message)
            else:
                raise AssertionError(f"line {block.line}: expected a ThemeError")
        else:
            Style.from_theme(path)
        loaded += 1
    return loaded
