"""The watercolour tutorial and the first map quote the scripts they teach, and run only scripts that exist.

A fenced code block that follows a `<!-- from examples/<stem>.py -->` marker, or a
`<!-- from examples/drawings/<name>.svg -->` marker, is a verbatim substring of that script
or drawing, so the page cannot drift from the code or file a reader runs. Every
rung script is quoted on its page, the rungs come in the painter's order under their
studio titles, and every `uv run python examples/<stem>.py` command a tutorial page shows
names a script in `examples/`.
"""

import re
from pathlib import Path

from support import REPO_ROOT
from support.examples import EXAMPLES_DIR

_TUTORIALS = REPO_ROOT / "docs" / "tutorials"
_WATERCOLOUR = _TUTORIALS / "paint-a-watercolour.md"
_FIRST_MAP = _TUTORIALS / "first-map.md"
_VECTOR = _TUTORIALS / "painting-with-python" / "vector-drawing.md"

#: The rung scripts in the painter's order, each with the heading its section carries.
_WATERCOLOUR_RUNGS: tuple[tuple[str, str], ...] = (
    ("paper", "Stretch the paper"),
    ("wash", "Lay a wash"),
    ("brush_stroke", "Pull a brush"),
    ("pigments", "Mix two pigments"),
    ("nib_line", "Take up the pen"),
    ("lettering", "Letter a name"),
    ("composition", "Compose the painting"),
)

_MARKED_BLOCK = re.compile(
    r"<!--\s*from examples/(?:(?P<stem>\w+)\.py|(?P<svg>drawings/\w+\.svg))\s*-->\s*\n"
    r"(?P<fence>```|~~~)[^\n]*\n(?P<code>.*?)\n(?P=fence)[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
_COMMAND = re.compile(r"uv run python examples/(?P<stem>[\w-]+)\.py")
_HEADING = re.compile(r"^#{2,3} (?P<title>.+?)\s*$", re.MULTILINE)


def _text(path: Path) -> str:
    """Return a tutorial page's text, or an empty string when the page is not written yet."""
    return path.read_text() if path.is_file() else ""


def _tutorial_pages() -> list[Path]:
    """Return the tutorial pages this slice owns."""
    return [_WATERCOLOUR, _FIRST_MAP, _VECTOR]


def test_every_marked_block_is_a_verbatim_part_of_its_script() -> None:
    """Each code block under a `from examples/...` marker appears unchanged in that script or drawing."""
    drifted: list[str] = []
    marked = 0
    for page in _tutorial_pages():
        for found in _MARKED_BLOCK.finditer(_text(page)):
            marked += 1
            name = found["svg"] or f"{found['stem']}.py"
            source = EXAMPLES_DIR / name
            if not source.is_file() or found["code"] not in source.read_text():
                drifted.append(f"{page.name}: {name}")
    assert marked, "no tutorial page quotes a script yet"
    assert not drifted, f"quoted code that is not in its script: {drifted}"


def test_the_vector_page_links_the_drawing_it_reads() -> None:
    """The vector drawing page links `examples/drawings/fell.svg`, which exists, instead of quoting it."""
    assert "examples/drawings/fell.svg" in _text(_VECTOR)
    assert (EXAMPLES_DIR / "drawings" / "fell.svg").is_file()


def test_every_watercolour_rung_is_quoted_on_its_page() -> None:
    """The watercolour page quotes each of the seven rung scripts at least once."""
    quoted = {found["stem"] for found in _MARKED_BLOCK.finditer(_text(_WATERCOLOUR))}
    missing = [stem for stem, _ in _WATERCOLOUR_RUNGS if stem not in quoted]
    assert not missing, f"rungs the watercolour page does not quote: {missing}"


def test_the_first_map_quotes_the_route_map_script() -> None:
    """The first map page quotes the route map script, the eighth rung."""
    quoted = {found["stem"] for found in _MARKED_BLOCK.finditer(_text(_FIRST_MAP))}
    assert "route_map" in quoted


def test_the_rungs_come_in_the_painters_order_under_their_studio_titles() -> None:
    """The watercolour page's section titles are the seven studio steps, in order."""
    titles = [found["title"] for found in _HEADING.finditer(_text(_WATERCOLOUR))]
    steps = [title for title in titles if title in {step for _, step in _WATERCOLOUR_RUNGS}]
    assert steps == [step for _, step in _WATERCOLOUR_RUNGS]


def test_every_run_command_names_an_existing_script() -> None:
    """Each `uv run python examples/<stem>.py` a tutorial page shows names a script in examples/."""
    shown = 0
    unknown: list[str] = []
    for page in _tutorial_pages():
        for found in _COMMAND.finditer(_text(page)):
            shown += 1
            if not (EXAMPLES_DIR / f"{found['stem']}.py").is_file():
                unknown.append(f"{page.name}: {found['stem']}")
    assert shown, "no tutorial page shows a run command yet"
    assert not unknown, f"commands that name a missing script: {unknown}"
