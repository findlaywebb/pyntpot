"""The site-page helpers read `mkdocs.yml` and Markdown the way the docs-truth checks need.

Each helper runs on inline text built here, except `site_pages`, which reads the real
`mkdocs.yml` and `docs/`, and `resolve_dotted`, which imports the real package.
"""

import inspect

import pytest

import pyntpot.ink
from pyntpot.maps.card import Card

from support import REPO_ROOT
from support.site_pages import (
    DOCS,
    MKDOCS,
    Block,
    NavEntry,
    excluded,
    fenced_blocks,
    links,
    nav,
    prose,
    resolve,
    resolve_dotted,
    site_pages,
)


def _mkdocs(exclude: str = "", nav_lines: str = "") -> str:
    """Return a small `mkdocs.yml` text with the given exclusion entries and nav lines."""
    parts = ["site_name: test\ndocs_dir: docs\n"]
    if exclude:
        parts.append("exclude_docs: |\n" + "".join(f"  {e}\n" for e in exclude.split()))
    parts.append("theme:\n  name: material\n")
    if nav_lines:
        parts.append("nav:\n" + nav_lines)
    return "".join(parts)


class TestPaths:
    """The helper's two anchors are the repository's own files."""

    def test_the_anchors_are_the_repository_config_and_docs(self) -> None:
        """`MKDOCS` is the repository's `mkdocs.yml` and `DOCS` its `docs/` directory."""
        assert MKDOCS == REPO_ROOT / "mkdocs.yml"
        assert DOCS == REPO_ROOT / "docs"


class TestExcluded:
    """`excluded` reads the `exclude_docs: |` block's entries."""

    def test_the_entries_are_read_in_order(self) -> None:
        """Each indented line of the block is one entry, in file order."""
        text = _mkdocs(exclude="README.md decisions/ runbooks/")
        assert excluded(text) == ("README.md", "decisions/", "runbooks/")

    def test_no_block_means_no_entries(self) -> None:
        """A config with no `exclude_docs` block excludes nothing."""
        assert excluded(_mkdocs()) == ()


class TestSitePages:
    """`site_pages` lists the real site's Markdown pages."""

    def test_the_pages_are_sorted_and_under_docs(self) -> None:
        """The pages are sorted and every one is a Markdown file under `docs/`."""
        pages = site_pages()
        assert pages == sorted(pages)
        assert all(p.suffix == ".md" and p.is_relative_to(DOCS) for p in pages)

    def test_excluded_files_and_directories_are_left_out(self) -> None:
        """No page is an excluded file or sits under an excluded directory."""
        relative = [p.relative_to(DOCS).as_posix() for p in site_pages()]
        assert "README.md" not in relative
        assert "architecture.md" not in relative
        assert not [r for r in relative if r.startswith(("decisions/", "issues/", "runbooks/"))]

    def test_the_front_page_and_a_nested_tutorial_are_pages(self) -> None:
        """The front page and a page two directories down are site pages."""
        pages = site_pages()
        assert DOCS / "index.md" in pages
        assert DOCS / "tutorials" / "painting-with-python" / "curves.md" in pages


class TestNav:
    """`nav` reads the nav's entries and the sections each sits in."""

    def test_titled_bare_and_nested_entries_are_read(self) -> None:
        """Titled and bare entries are read at every depth with their section path."""
        text = _mkdocs(
            nav_lines=(
                "  - Home: index.md\n"
                "  - Tutorials:\n"
                "      - tutorials/index.md\n"
                "      - Paint: tutorials/paint.md\n"
                "      - Painting with Python:\n"
                "          - tutorials/pwp/index.md\n"
                "          - Curves: tutorials/pwp/curves.md\n"
                "      - First map: tutorials/first-map.md\n"
                "  - Gallery: gallery.md\n"
            )
        )
        assert nav(text) == [
            NavEntry("index.md", ()),
            NavEntry("tutorials/index.md", ("Tutorials",)),
            NavEntry("tutorials/paint.md", ("Tutorials",)),
            NavEntry("tutorials/pwp/index.md", ("Tutorials", "Painting with Python")),
            NavEntry("tutorials/pwp/curves.md", ("Tutorials", "Painting with Python")),
            NavEntry("tutorials/first-map.md", ("Tutorials",)),
            NavEntry("gallery.md", ()),
        ]

    def test_the_real_nav_opens_with_the_front_page(self) -> None:
        """The repository's nav parses, and its first entry is the front page."""
        entries = nav(MKDOCS.read_text())
        assert entries[0] == NavEntry("index.md", ())


class TestFencedBlocks:
    """`fenced_blocks` finds every fence, its language, code, marker and line."""

    def test_a_marker_on_the_line_before_the_fence(self) -> None:
        """A comment directly above the fence is the block's marker."""
        text = "Intro.\n<!-- from examples/paper.py -->\n```python\nsheet = 1\n```\n"
        assert fenced_blocks(text) == [
            Block("python", "sheet = 1", "<!-- from examples/paper.py -->", 3)
        ]

    def test_a_marker_with_a_blank_line_before_the_fence(self) -> None:
        """A comment with a blank line between it and the fence is still the marker."""
        text = "<!-- from examples/curves.py -->\n\n```python\nrose()\n```\n"
        assert fenced_blocks(text)[0].marker == "<!-- from examples/curves.py -->"

    def test_a_block_with_prose_above_has_no_marker(self) -> None:
        """A block whose nearest non-blank line above is prose has no marker."""
        text = "<!-- a comment -->\nRun this:\n\n~~~console\n$ uv run pytest\n~~~\n"
        assert fenced_blocks(text) == [Block("console", "$ uv run pytest", None, 4)]

    def test_an_indented_fence_is_dedented_by_its_own_indent_only(self) -> None:
        """A fence in a list item is found, and its code keeps indentation past the fence's."""
        text = "1. Paint it:\n\n   ```python\n   def paint():\n       return 1\n   ```\n"
        assert fenced_blocks(text) == [Block("python", "def paint():\n    return 1", None, 3)]

    def test_a_block_quoting_indented_lines_keeps_them_indented(self) -> None:
        """A margin fence quoting indented script lines keeps their indentation."""
        text = "```python\n        mask = cover & inside\n        wash(mask)\n```\n"
        assert fenced_blocks(text)[0].code == "        mask = cover & inside\n        wash(mask)"

    def test_every_block_on_a_page_is_found_in_order(self) -> None:
        """Two blocks, one with no language, come back in page order."""
        text = "```\nplain\n```\n\nText.\n\n```bash\nls\n```\n"
        blocks = fenced_blocks(text)
        assert [(b.lang, b.code, b.line) for b in blocks] == [("", "plain", 1), ("bash", "ls", 7)]


class TestProse:
    """`prose` is the page without its fenced blocks."""

    def test_margin_and_indented_blocks_are_removed(self) -> None:
        """Both a margin fence and an indented fence disappear with their code."""
        text = "Before.\n```python\nx = 1\n```\n- item\n\n  ~~~\n  y\n  ~~~\nAfter.\n"
        kept = prose(text)
        assert "Before." in kept
        assert "After." in kept
        assert "- item" in kept
        assert "x = 1" not in kept
        assert "y" not in kept.split()
        assert "```" not in kept
        assert "~~~" not in kept


class TestLinks:
    """`links` lists link targets in page order, images left out."""

    def test_targets_in_order_with_duplicates_and_no_images(self) -> None:
        """Links come in page order, a repeat is kept, an image is not a link."""
        text = (
            "See [Curves](curves.md) and ![a fern](../images/fern.webp).\n"
            "Then [the wash](../explanation/wash.md#pool) and [Curves](curves.md).\n"
            "Out: [site](https://example.org/x.md).\n"
        )
        assert links(text) == [
            "curves.md",
            "../explanation/wash.md#pool",
            "curves.md",
            "https://example.org/x.md",
        ]

    def test_a_link_inside_a_code_block_is_not_a_link(self) -> None:
        """A link written inside a fenced block is code, not a link."""
        assert links("```markdown\n[x](x.md)\n```\n") == []


class TestResolve:
    """`resolve` turns a relative link into the page it names."""

    def test_a_relative_link_with_a_fragment(self) -> None:
        """A relative link resolves against the page's directory with the fragment dropped."""
        page = DOCS / "tutorials" / "painting-with-python" / "curves.md"
        target = resolve(page, "../paint-a-watercolour.md#take-up-the-pen")
        assert target == DOCS / "tutorials" / "paint-a-watercolour.md"

    def test_a_link_up_two_levels(self) -> None:
        """A link two directories up resolves to the page it names."""
        page = DOCS / "tutorials" / "painting-with-python" / "pictures.md"
        assert resolve(page, "../../how-to/index.md") == DOCS / "how-to" / "index.md"

    @pytest.mark.parametrize(
        "href",
        ["https://example.org/a.md", "mailto:someone@example.org", "/pyntpot/index.md"],
        ids=["https", "mailto", "site-absolute"],
    )
    def test_an_absolute_link_resolves_to_none(self, href: str) -> None:
        """A link with a scheme or a leading slash names no page in the tree."""
        assert resolve(DOCS / "index.md", href) is None


class TestResolveDotted:
    """`resolve_dotted` imports the longest module prefix, then reads attributes."""

    def test_an_exported_name(self) -> None:
        """A name a layer exports resolves to that object."""
        assert resolve_dotted("pyntpot.ink.Sheet") is pyntpot.ink.Sheet

    def test_a_private_module_path(self) -> None:
        """A name in a private module resolves through that module."""
        assert resolve_dotted("pyntpot.maps.card.Card") is Card

    def test_a_module_shadowing_a_function_resolves_to_the_module(self) -> None:
        """`unittest.main` is the module, not the package attribute of the same name."""
        assert inspect.ismodule(resolve_dotted("unittest.main"))

    def test_a_missing_part_raises_naming_the_path(self) -> None:
        """A path whose last part does not exist raises `LookupError` naming the path."""
        with pytest.raises(LookupError, match=r"pyntpot\.ink\.NoSuchName"):
            resolve_dotted("pyntpot.ink.NoSuchName")

    def test_a_missing_package_raises_naming_the_path(self) -> None:
        """A path no prefix of which imports raises `LookupError` naming the path."""
        with pytest.raises(LookupError, match=r"nosuchpackage\.thing"):
            resolve_dotted("nosuchpackage.thing")
