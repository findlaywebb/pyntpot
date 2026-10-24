"""The README keeps its order, and its Python quick start is a verbatim excerpt of `examples/wash.py`.

The README is the PyPI page, so it is written once and checked here: the tagline, the hero,
the lede and the five badges come in the prescribed order before the first section, the
sections follow in the prescribed order, and the code block under the
`<!-- from examples/<stem>.py -->` marker is a substring of that script made of whole
top-level statements, so it cannot drift from the code a reader runs.
"""

import ast
import re

from support import REPO_ROOT
from support.examples import EXAMPLES_DIR

_README = (REPO_ROOT / "README.md").read_text()

_TAGLINE = "Hand-drawn watercolour and pen-and-ink painting for Python, with route maps."
_LEDE = "Lay a wash, pull a brush, letter a name."
_SECTIONS = [
    "What it is",
    "Gallery",
    "Install",
    "Quick start",
    "Crediting the data",
    "Documentation",
    "Status",
    "Licence",
]
_BADGES = [
    "[![PyPI](https://img.shields.io/pypi/v/pyntpot)](https://pypi.org/project/pyntpot/)",
    "[![Python](https://img.shields.io/pypi/pyversions/pyntpot)](https://pypi.org/project/pyntpot/)",
    (
        "[![CI](https://github.com/findlaywebb/pyntpot/actions/workflows/ci.yml/badge.svg)]"
        "(https://github.com/findlaywebb/pyntpot/actions/workflows/ci.yml)"
    ),
    (
        "[![Licence](https://img.shields.io/pypi/l/pyntpot)]"
        "(https://github.com/findlaywebb/pyntpot/blob/main/LICENSE)"
    ),
    (
        "[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)]"
        "(https://codspeed.io/findlaywebb/pyntpot)"
    ),
]
_MARKED_BLOCK = re.compile(
    r"<!--\s*from examples/(?P<stem>\w+)\.py\s*-->\s*\n```python\n(?P<code>.*?)\n```", re.DOTALL
)
_HEADING = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)


def test_the_front_of_the_readme_comes_in_the_prescribed_order() -> None:
    """The wordmark, the tagline, the hero, the second picture, the lede and the badges come before the first section."""
    positions = [
        _README.index(marker)
        for marker in (
            "docs/images/word.webp",
            _TAGLINE,
            "docs/images/hero.webp",
            "docs/images/painting-with-python/derwentwater.webp",
            _LEDE,
            _BADGES[0],
            "## What it is",
        )
    ]
    assert positions == sorted(positions)


def test_the_badges_are_the_five_prescribed_lines_in_order() -> None:
    """The five badge lines appear exactly as prescribed, one per line, in order."""
    lines = _README.splitlines()
    assert [i for i, line in enumerate(lines) if line in _BADGES] == [
        lines.index(_BADGES[0]) + n for n in range(5)
    ]
    assert [line for line in lines if line in _BADGES] == _BADGES


def test_the_sections_come_in_the_prescribed_order() -> None:
    """The README's second-level headings are the prescribed sections, in order."""
    assert [found["title"] for found in _HEADING.finditer(_README)] == _SECTIONS


def test_the_python_quick_start_is_a_verbatim_excerpt_of_the_wash_script() -> None:
    """The marked Python block is whole top-level statements of `examples/wash.py`, unchanged."""
    blocks = list(_MARKED_BLOCK.finditer(_README))
    assert [found["stem"] for found in blocks] == ["wash"]
    code = blocks[0]["code"]
    script = (EXAMPLES_DIR / "wash.py").read_text()
    assert code in script
    tree = ast.parse(script)
    lines = script.splitlines()
    start = script[: script.index(code)].count("\n")
    end = start + code.count("\n") + 1
    covered = [
        node
        for node in tree.body
        if node.lineno - 1 >= start and (node.end_lineno or node.lineno) <= end
    ]
    assert ast.parse(code).body, "the block holds no statements"
    assert len(covered) == len(ast.parse(code).body), "the block cuts a statement in two"
    assert lines[start:end] == code.splitlines()


def test_the_quick_start_calls_the_excerpt_so_it_runs_as_pasted() -> None:
    """A second Python block after the excerpt calls `main`, so a reader who pastes both gets a picture."""
    found = _MARKED_BLOCK.search(_README)
    assert found is not None
    after = _README[found.end() :]
    assert 'main(Path("out"))' in after.split("##", 1)[0]
