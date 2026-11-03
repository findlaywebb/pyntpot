"""`GLOSSARY.md` holds the canonical terms, and the site's glossary page and tooltips match it.

`TestParse` runs the generator's reader and renderers on inline text; `TestTheGlossary`
checks the real file's terms, tooltips, retired words and code names; `TestGeneratedFiles`
checks the two committed files the generator writes, and the site configuration that shows
them.
"""

import re
import string
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from support import REPO_ROOT
from support.glossary import (
    EVERYDAY_WORDS,
    REGENERATE,
    Glossary,
    Retired,
    Term,
    abbreviations,
    anchor,
    glossary_page,
    parse,
    plain,
)
from support.site_pages import MKDOCS, resolve_dotted, site_pages

_GLOSSARY = REPO_ROOT / "GLOSSARY.md"
_PAGE = REPO_ROOT / "docs" / "reference" / "glossary.md"
_ABBREVIATIONS = REPO_ROOT / "docs" / "includes" / "abbreviations.md"

_READER_HEADER = "| Term | Meaning | In the code | Tooltip |\n| --- | --- | --- | --- |\n"
_CONTRIBUTOR_HEADER = "| Term | Meaning | In the code |\n| --- | --- | --- |\n"
_COMMENT = (
    "<!-- Generated from GLOSSARY.md by tests/support/glossary.py. Edit GLOSSARY.md, then run: "
    "PYTHONPATH=tests uv run python -m support.glossary -->"
)
_CURLY_APOSTROPHE = "\u2019"
_RETIRED_HEADER = "| Retired | Say instead |\n| --- | --- |\n"


def _glossary_text(
    reader_rows: str = "| tooth | The paper's `paper` height. | `pyntpot.ink.Sheet` | tooth, Tooth |\n",
    contributor_rows: str = "| ink pad | One accumulator. | `pyntpot.ink.pad.InkPad` |\n",
    retired_rows: str = "| label plate | nib plate |\n",
    reader_header: str = _READER_HEADER,
    extra: str = "",
) -> str:
    """Return a small `GLOSSARY.md` text in the prescribed shape, with the given rows."""
    return (
        "# Glossary\n\nOne canonical name per concept.\n\n"
        "## Terms a reader meets\n\n### Painting\n\n"
        f"{reader_header}{reader_rows}\n"
        "## Terms a contributor meets\n\n"
        f"{_CONTRIBUTOR_HEADER}{contributor_rows}\n"
        "## Retired words\n\n"
        f"{_RETIRED_HEADER}{retired_rows}{extra}"
    )


def _read(path: Path) -> str:
    """Return a repository file's text, or an empty string when it does not exist."""
    return path.read_text(encoding="utf-8") if path.exists() else ""


@pytest.fixture(scope="module")
def glossary() -> Glossary:
    """The parsed `GLOSSARY.md`, immutable."""
    return parse(_read(_GLOSSARY))


class TestParse:
    """The generator reads the prescribed shape, refuses any other, and renders the two files."""

    def test_the_three_sections_parse(self):
        """A reader group, the contributor table and the retired words parse into their records."""
        reader = (
            "| tooth | High `paper`. | `pyntpot.ink.Sheet`, `pyntpot.ink.Canvas` | tooth, Tooth |\n"
        )
        reader += "| sheet | The paper's fields. | | no |\n"
        glossary = parse(_glossary_text(reader_rows=reader))
        assert glossary == Glossary(
            terms=(
                Term(
                    name="tooth",
                    meaning="High `paper`.",
                    code=("pyntpot.ink.Sheet", "pyntpot.ink.Canvas"),
                    tooltip=("tooth", "Tooth"),
                    audience="reader",
                    group="Painting",
                ),
                Term(
                    name="sheet",
                    meaning="The paper's fields.",
                    code=(),
                    tooltip=(),
                    audience="reader",
                    group="Painting",
                ),
                Term(
                    name="ink pad",
                    meaning="One accumulator.",
                    code=("pyntpot.ink.pad.InkPad",),
                    tooltip=(),
                    audience="contributor",
                    group="",
                ),
            ),
            retired=(Retired(word="label plate", instead="nib plate"),),
        )

    @pytest.mark.parametrize(
        ("text", "line"),
        [
            (_glossary_text(extra="\n## Further reading\n"), 25),
            (
                _glossary_text(reader_header="| Term | Meaning | Tooltip |\n| --- | --- | --- |\n"),
                9,
            ),
            (_glossary_text(reader_rows="| tooth | High. | tooth |\n"), 11),
            (_glossary_text(reader_rows="| tooth | High. | `pyntpot.ink.Sheet` |  |\n"), 11),
            (_glossary_text(extra="\n### Lettering\n"), 25),
        ],
        ids=[
            "unknown-section",
            "wrong-table-header",
            "wrong-cell-count",
            "empty-reader-tooltip",
            "group-outside-the-reader-section",
        ],
    )
    def test_a_malformed_glossary_raises_naming_the_line(self, text, line):
        """Each malformed shape raises `ValueError` naming the offending line."""
        with pytest.raises(ValueError, match=rf"\bline {line}\b"):
            parse(text)

    @pytest.mark.parametrize(
        ("markdown", "expected"),
        [
            ("The sheet's `paper` field.", "The sheet's paper field."),
            ("See [the wash](../explanation/how-the-wash-works.md) here.", "See the wash here."),
            ("A **strong** and *soft* edge.", "A strong and soft edge."),
            ("  Two\n   lines  ", "Two lines"),
        ],
        ids=["backticks", "link", "emphasis", "whitespace"],
    )
    def test_plain_drops_markup(self, markdown, expected):
        """`plain` drops backticks, link targets and emphasis, and collapses whitespace."""
        assert plain(markdown) == expected

    @pytest.mark.parametrize(
        ("term", "expected"),
        [
            ("tooth", "term-tooth"),
            ("nib plate", "term-nib-plate"),
            ("painter's pigment", "term-painter-s-pigment"),
            ("Kubelka-Munk", "term-kubelka-munk"),
            (" -route ink- ", "term-route-ink"),
        ],
        ids=["one-word", "two-words", "apostrophe", "capitals-and-hyphen", "edges-stripped"],
    )
    def test_anchor_slugs_the_term(self, term, expected):
        """`anchor` lowercases the term and joins its runs of letters and digits with `-`."""
        assert anchor(term) == expected

    @given(st.tuples(st.text(), st.sampled_from(string.ascii_letters), st.text()).map("".join))
    def test_anchor_is_always_a_valid_slug(self, term):
        """For any term holding an ASCII letter, `anchor` gives `term-` and dash-joined runs of `[a-z0-9]`."""
        assert re.fullmatch(r"term-[a-z0-9]+(-[a-z0-9]+)*", anchor(term))

    def test_the_page_renders_reader_terms_only(self):
        """The glossary page is the pinned text: reader terms with anchors, no contributor term, no retired word."""
        reader = "| tooth | High `paper`. | `pyntpot.ink.Sheet` | tooth, Tooth |\n"
        reader += "| sheet | The fields. | | no |\n"
        page = glossary_page(parse(_glossary_text(reader_rows=reader)))
        assert page == (
            f"{_COMMENT}\n"
            "# Glossary\n"
            "\n"
            "Every term these docs use, what it means and where it lives in the code. The docs "
            "use one name for each of these and no other. A term underlined on a page shows its "
            "meaning when you point at it. The source is "
            "[GLOSSARY.md](https://github.com/findlaywebb/pyntpot/blob/main/GLOSSARY.md) in the "
            "repository.\n"
            "\n"
            "## Painting\n"
            "\n"
            "| Term | Meaning | In the code |\n"
            "| --- | --- | --- |\n"
            '| <span id="term-tooth"></span>tooth | High `paper`. | `pyntpot.ink.Sheet` |\n'
            '| <span id="term-sheet"></span>sheet | The fields. |  |\n'
        )

    def test_the_abbreviations_are_blank_line_separated(self):
        """The abbreviations text is the pinned text: one plain definition per tooltip form, a blank line between."""
        reader = "| tooth | High `paper`. | `pyntpot.ink.Sheet` | tooth, Tooth |\n"
        reader += "| sheet | The fields. | | no |\n"
        text = abbreviations(parse(_glossary_text(reader_rows=reader)))
        assert text == (f"{_COMMENT}\n\n*[tooth]: High paper.\n\n*[Tooth]: High paper.\n")


class TestTheGlossary:
    """The real `GLOSSARY.md` is consistent: unique terms and forms, live code names, sound retired words."""

    def test_it_parses_into_three_sections(self, glossary):
        """The file holds reader terms, contributor terms and retired words."""
        audiences = {term.audience for term in glossary.terms}
        assert audiences == {"reader", "contributor"}
        assert glossary.retired

    def test_terms_are_unique(self, glossary):
        """No term appears twice, case-insensitively, across both sections."""
        names = [term.name.lower() for term in glossary.terms]
        assert sorted({n for n in names if names.count(n) > 1}) == []

    def test_tooltip_forms_are_unique_and_not_everyday_words(self, glossary):
        """Every tooltip form appears once in the glossary and none is an everyday word."""
        forms = [form for term in glossary.terms for form in term.tooltip]
        assert sorted({f for f in forms if forms.count(f) > 1}) == []
        assert sorted(f for f in forms if f.lower() in EVERYDAY_WORDS) == []

    def test_no_retired_word_is_a_term(self, glossary):
        """A retired word is never also a term."""
        names = {term.name.lower() for term in glossary.terms}
        assert [r.word for r in glossary.retired if r.word.lower() in names] == []

    def test_every_say_instead_ends_in_a_term(self, glossary):
        """Each retired word's replacement ends in a term as a whole word, a qualifier before it allowed."""
        names = [term.name for term in glossary.terms]
        orphans = [
            r.instead
            for r in glossary.retired
            if not any(re.search(rf"\b{re.escape(n)}$", r.instead, re.IGNORECASE) for n in names)
        ]
        assert orphans == []

    def test_every_code_name_resolves(self, glossary):
        """Every dotted name in an "In the code" cell, reader or contributor, resolves at runtime."""
        missing = []
        for term in glossary.terms:
            for name in term.code:
                try:
                    resolve_dotted(name)
                except LookupError:
                    missing.append(f"{term.name}: {name}")
        assert missing == []

    def test_no_site_page_has_a_curly_apostrophe(self):
        """No site page writes a curly apostrophe, which a tooltip form spelt with `'` would not underline."""
        curly = [
            str(p.relative_to(REPO_ROOT)) for p in site_pages() if _CURLY_APOSTROPHE in _read(p)
        ]
        assert curly == []


class TestGeneratedFiles:
    """The committed glossary page and abbreviations match `GLOSSARY.md`, and the site shows them."""

    def test_the_glossary_page_is_generated(self):
        """`docs/reference/glossary.md` is exactly what the generator writes from `GLOSSARY.md`."""
        expected = glossary_page(parse(_read(_GLOSSARY)))
        assert _read(_PAGE) == expected, f"docs/reference/glossary.md is stale; run: {REGENERATE}"

    def test_the_abbreviations_are_generated(self):
        """`docs/includes/abbreviations.md` is exactly what the generator writes from `GLOSSARY.md`."""
        expected = abbreviations(parse(_read(_GLOSSARY)))
        assert _read(_ABBREVIATIONS) == expected, (
            f"docs/includes/abbreviations.md is stale; run: {REGENERATE}"
        )

    def test_the_site_underlines_tooltip_forms(self):
        """`mkdocs.yml` enables `abbr`, appends the abbreviations to every page and styles them as tooltips."""
        text = MKDOCS.read_text(encoding="utf-8")
        assert re.search(r"^  - abbr$", text, re.MULTILINE)
        assert re.search(
            r"^  - pymdownx\.snippets:\n"
            r"(?:      \S.*\n)*"
            r"      auto_append: \[docs/includes/abbreviations\.md\]\n",
            text,
            re.MULTILINE,
        )
        assert re.search(
            r"^  - pymdownx\.snippets:\n(?:      \S.*\n)*      check_paths: true\n",
            text,
            re.MULTILINE,
        )
        assert re.search(r"^    - content\.tooltips$", text, re.MULTILINE)
