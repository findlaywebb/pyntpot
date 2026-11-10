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

import pytest

from pyntpot.ink import Reserve
from pyntpot.maps import Palette, Style, ThemeError

from support.site_pages import DOCS, fenced_blocks

EXAMPLE_THEMES = DOCS.parent / "examples" / "themes"

_THEME_PAGE = DOCS / "how-to" / "write-a-theme.md"
_EFFECTS_PAGE = DOCS / "how-to" / "case-light-or-shadow-a-line.md"
_MARKER = re.compile(r"<!-- (?P<kind>theme|palette): (?P<name>\S+)(?P<broken> broken)? -->")


def test_every_yaml_block_loads_or_fails_as_marked(tmp_path: Path) -> None:
    """Each yaml block loads through the theme checker, or raises `ThemeError` with messages the page prints."""
    assert len(_check_page(_THEME_PAGE, tmp_path / "theme")) >= 14
    assert len(_check_page(_EFFECTS_PAGE, tmp_path / "effects")) >= 3


@pytest.mark.parametrize("page", [_THEME_PAGE, _EFFECTS_PAGE], ids=["write-a-theme", "effects"])
def test_the_reserve_and_union_blocks_set_what_the_page_says(page: Path, tmp_path: Path) -> None:
    """Each page has a block that gives `road_major` a reserve and one that unions it with `lane`."""
    styles = [
        loaded for loaded in _check_page(page, tmp_path / "page") if isinstance(loaded, Style)
    ]
    reserves = [
        stack.effects
        for style in styles
        if (stack := style.basemap.line_effects.get("road_major")) is not None
        and any(isinstance(effect, Reserve) for effect in stack.effects)
    ]
    assert (Reserve(width_px=2.0, pool=0.3),) in reserves
    unions = [set(union) for style in styles for union in style.basemap.casing_unions]
    assert {"road_major", "lane"} in unions


def _check_page(page: Path, directory: Path) -> list[Style | Palette | None]:
    """Load or fail each yaml block of `page` saved in `directory`, beside the example themes.

    Returns what each checked block loaded, `None` for a block that failed as marked.
    """
    text = page.read_text()
    shutil.copytree(EXAMPLE_THEMES, directory)
    loaded: list[Style | Palette | None] = []
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
            loaded.append(Palette.from_file(path))
        elif broken:
            try:
                Style.from_theme(path)
            except ThemeError as error:
                for problem in error.problems:
                    assert problem.message in text, (block.line, problem.message)
            else:
                raise AssertionError(f"line {block.line}: expected a ThemeError")
            loaded.append(None)
        else:
            loaded.append(Style.from_theme(path))
    return loaded
