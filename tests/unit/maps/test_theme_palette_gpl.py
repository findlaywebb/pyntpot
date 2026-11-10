"""The `.gpl` reader and writer: normal forms, located refusals and the export rows."""

from pathlib import Path

import pytest

from pyntpot.ink import PIGMENT_REGISTRY, pigment
from pyntpot.maps.theme_palette_gpl import alias_of, parse_gpl, write_gpl

PATH = Path("p.gpl")
HEADER = "GIMP Palette\nName: test\nColumns: 0\n#\n"


def _parse(rows: str):
    """Parse the `.gpl` text of `rows` under the standard header."""
    return parse_gpl(PATH, HEADER + rows)


def _messages(rows: str) -> list[tuple[int | None, str]]:
    """The line and message of every problem in `rows`."""
    return [(p.line, p.message) for p in _parse(rows)[1]]


class TestAliasOf:
    """A `.gpl` name reads as an alias."""

    @pytest.mark.parametrize(
        ("name", "alias"),
        [
            ("Sky Blue", "sky_blue"),
            ("sky-blue", "sky_blue"),
            ("  Sky  --  Blue ", "sky_blue"),
            ("Burnt_Sienna", "burnt_sienna"),
            ("2 Blue", "2_blue"),
            ("!!!", ""),
        ],
        ids=["space", "hyphen", "runs", "underscore", "digit", "nothing"],
    )
    def test_the_normal_form(self, name: str, alias: str) -> None:
        """Lower case, each run of other characters one `_`, stripped."""
        assert alias_of(name) == alias


class TestImport:
    """Rows become anonymous pigments."""

    def test_a_row_is_an_anonymous_pigment_of_its_hex(self) -> None:
        """`43 61 143 Sky Blue` is `sky_blue`, the anonymous pigment of `#2b3d8f`."""
        aliases, problems = _parse("  43  61 143\tSky Blue\n")
        assert problems == ()
        assert aliases == {"sky_blue": pigment("#2b3d8f")}
        assert aliases["sky_blue"].transparency is None

    def test_comments_blank_lines_and_metadata_are_skipped(self) -> None:
        """Only rows make aliases."""
        aliases, problems = _parse("\n# note\n0 0 0 black\n")
        assert (list(aliases), problems) == (["black"], ())


class TestRefusals:
    """Each refusal is located at its row's line, never a drop."""

    def test_a_missing_header_is_refused(self) -> None:
        """A file that does not start with the header is refused at line 1."""
        _, problems = parse_gpl(PATH, "0 0 0 black\n")
        assert [(p.line, p.message) for p in problems] == [
            (1, "a .gpl file starts with the line 'GIMP Palette'")
        ]

    def test_a_row_with_no_name(self) -> None:
        """Three channels and no name is refused."""
        assert _messages("0 0 0\n") == [(5, "'0 0 0' has no name")]

    @pytest.mark.parametrize(
        "row", ["0 0 x name", "1 2", "-1 0 0 a"], ids=["word", "short", "sign"]
    )
    def test_a_row_that_is_no_row(self, row: str) -> None:
        """A row without three whole channels is refused."""
        assert _messages(row + "\n") == [(5, f"{row!r} is not a row of three channels and a name")]

    def test_a_channel_above_255(self) -> None:
        """A channel above 255 is refused."""
        assert _messages("256 0 0 red\n") == [(5, "'256 0 0 red' has a channel above 255")]

    def test_a_name_starting_with_a_digit(self) -> None:
        """'2 Blue' reads as '2_blue', which is no alias."""
        assert _messages("0 0 255 2 Blue\n") == [
            (5, "'2 Blue' reads as '2_blue'; an alias starts with a letter")
        ]

    def test_two_names_with_one_alias_name_the_first_line(self) -> None:
        """'Sky Blue' and 'sky-blue' both read as 'sky_blue', and the first row's line is named."""
        assert _messages("1 1 1 Sky Blue\n2 2 2 sky-blue\n") == [
            (6, "'Sky Blue' (line 5) and 'sky-blue' both read as 'sky_blue'")
        ]

    def test_a_built_in_pigment_name(self) -> None:
        """A name equal to a built-in pigment is refused."""
        assert _messages("1 1 1 Ultramarine\n") == [
            (
                5,
                "'Ultramarine' reads as 'ultramarine', a built-in pigment; an alias needs a name of its own",
            )
        ]

    def test_the_good_rows_are_still_read(self) -> None:
        """A bad row does not stop the others being read."""
        aliases, problems = _parse("1 1 1 ok\n0 0 0\n")
        assert (list(aliases), len(problems)) == (["ok"], 1)


class TestExport:
    """Rows are `R G B<TAB>name` under the header."""

    def test_the_rows_are_padded_channels_a_tab_and_the_name(self) -> None:
        """A row is three right-aligned channels, a tab and the alias."""
        text = write_gpl("mine", {"sky": pigment("#2b3d8f")})
        assert text == "GIMP Palette\nName: mine\nColumns: 0\n#\n 43  61 143\tsky\n"

    def test_it_drops_transparency_and_colour_index(self) -> None:
        """Exporting then importing gives anonymous pigments of the same colours."""
        aliases, problems = parse_gpl(PATH, write_gpl("p", {"sky": pigment("cerulean")}))
        assert problems == ()
        assert aliases["sky"] == pigment(str(pigment("cerulean").colour))

    def test_the_registry_export_lists_every_pigment_in_order(self) -> None:
        """Every registry name is a row, in registry order."""
        rows = write_gpl("r", {n: PIGMENT_REGISTRY.get(n) for n in PIGMENT_REGISTRY.names()})
        names = [row.split("\t")[1] for row in rows.splitlines()[4:]]
        assert names == list(PIGMENT_REGISTRY.names())
