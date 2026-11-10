"""`Palette`: packaged and file palettes, `.gpl` in and out, and a theme's `palette:` key."""

from pathlib import Path

import pytest

from pyntpot.ink import PIGMENT_REGISTRY, pigment
from pyntpot.maps import Palette, Style, ThemeError

from support.theme_files import write_theme


def _problems(path: Path) -> list[tuple[Path, int | None, str]]:
    """The file, line and message of every problem loading the theme at `path` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(path)
    return [(p.path, p.line, p.message) for p in caught.value.problems]


class TestPackaged:
    """The palettes the package ships."""

    def test_names_lists_the_packaged_palettes(self) -> None:
        """`plain` is the packaged palette."""
        assert Palette.names() == ("plain",)

    def test_plain_maps_each_word_to_its_built_in_pigment(self) -> None:
        """`plain.blue` is ultramarine itself, transparency and Colour Index included."""
        plain = Palette.named("plain")
        assert plain.name == "plain"
        assert plain.pigments["blue"] == pigment("ultramarine")
        assert plain.pigments["blue"].transparency == pigment("ultramarine").transparency

    def test_plain_has_the_ten_pinned_aliases(self) -> None:
        """The ten colour words and their pigments, in file order."""
        assert {k: v.name for k, v in Palette.named("plain").pigments.items()} == {
            "blue": "ultramarine",
            "sky": "cerulean",
            "green": "sap_green",
            "brown": "burnt_sienna",
            "orange": "raw_sienna",
            "ochre": "yellow_ochre",
            "red": "quinacridone_rose",
            "maroon": "perylene_maroon",
            "navy": "indigo",
            "grey": "paynes_grey",
        }

    def test_an_unknown_name_suggests_the_nearest(self) -> None:
        """`plan` is a located error naming `plain`."""
        with pytest.raises(ThemeError) as caught:
            Palette.named("plan")
        assert caught.value.problems[0].message == (
            "no palette named 'plan'; did you mean plain?; available: plain"
        )


class TestFromFile:
    """`.yaml` and `.gpl` files."""

    def test_a_yaml_palette_to_a_hex_holds_the_anonymous_pigment(self, tmp_path: Path) -> None:
        """An alias to a hex holds `pigment("#...")`."""
        path = write_theme(tmp_path, "mine.yaml", "colours:\n  moss: '#ABCDEF'\n  sea: cerulean\n")
        palette = Palette.from_file(path)
        assert palette.name == "mine"
        assert palette.pigments == {"moss": pigment("#abcdef"), "sea": pigment("cerulean")}

    def test_a_yaml_palette_holds_only_colours(self, tmp_path: Path) -> None:
        """Another top-level key is a located error at its line, in the palette file."""
        path = write_theme(tmp_path, "mine.yaml", "colours:\n  moss: cerulean\npaper: {}\n")
        with pytest.raises(ThemeError) as caught:
            Palette.from_file(path)
        (problem,) = caught.value.problems
        assert (problem.path, problem.line, problem.message) == (path, 3, "unknown key")

    def test_a_palette_alias_to_an_alias_is_refused(self, tmp_path: Path) -> None:
        """The alias rules hold in a palette file."""
        path = write_theme(tmp_path, "mine.yaml", "colours:\n  a: cerulean\n  b: a\n")
        with pytest.raises(ThemeError) as caught:
            Palette.from_file(path)
        assert [(p.line, p.message) for p in caught.value.problems] == [
            (3, "'a' is an alias; an alias names a pigment or a hex")
        ]

    def test_a_gpl_file_imports_anonymous_pigments(self, tmp_path: Path) -> None:
        """Every pigment a `.gpl` import yields has no transparency."""
        path = write_theme(
            tmp_path, "mine.gpl", "GIMP Palette\nName: x\n#\n 43  61 143\tSky Blue\n"
        )
        palette = Palette.from_file(path)
        assert palette.pigments == {"sky_blue": pigment("#2b3d8f")}
        assert all(p.transparency is None for p in palette.pigments.values())

    def test_a_bad_gpl_row_is_located_in_the_gpl_file(self, tmp_path: Path) -> None:
        """A bad row is a problem of the `.gpl` file, at the row's line."""
        path = write_theme(tmp_path, "mine.gpl", "GIMP Palette\n0 0 0\n")
        with pytest.raises(ThemeError) as caught:
            Palette.from_file(path)
        (problem,) = caught.value.problems
        assert (problem.path, problem.line) == (path, 2)

    def test_another_suffix_is_refused(self, tmp_path: Path) -> None:
        """A palette file ends in `.yaml` or `.gpl`."""
        with pytest.raises(ThemeError) as caught:
            Palette.from_file(tmp_path / "mine.txt")
        assert caught.value.problems[0].message == "a palette file ends in .yaml or .gpl"

    def test_a_missing_file_is_refused(self, tmp_path: Path) -> None:
        """A missing file is a located problem naming it."""
        with pytest.raises(ThemeError) as caught:
            Palette.from_file(tmp_path / "gone.gpl")
        assert caught.value.problems[0].message == f"no such palette file: {tmp_path / 'gone.gpl'}"


class TestGpl:
    """Export, and the registry export."""

    def test_to_gpl_writes_each_alias_with_its_colour(self) -> None:
        """A palette exports its aliases and their pigments' hex."""
        text = Palette("t", {"sky": pigment("cerulean")}).to_gpl()
        assert text.splitlines()[-1] == " 42 122 176\tsky"

    def test_the_registry_export_lists_all_pigments_in_registry_order(self) -> None:
        """`registry_gpl()` has one row per built-in pigment under its canonical name."""
        rows = Palette.registry_gpl().splitlines()[4:]
        assert [row.split("\t")[1] for row in rows] == list(PIGMENT_REGISTRY.names())
        assert len(rows) == len(PIGMENT_REGISTRY.names())

    def test_the_registry_export_is_no_palette_a_theme_can_read_back(self, tmp_path: Path) -> None:
        """Importing it refuses the built-in names."""
        path = write_theme(tmp_path, "all.gpl", Palette.registry_gpl())
        with pytest.raises(ThemeError):
            Palette.from_file(path)


class TestThemePaletteKey:
    """A theme's `palette:`."""

    def test_a_packaged_name_puts_its_aliases_in_scope(self, tmp_path: Path) -> None:
        """`palette: plain` lets a field say `sky`."""
        path = write_theme(tmp_path, "t.yaml", "palette: plain\nroute_ink:\n  colour: sky\n")
        assert Style.from_theme(path).route_ink.colour == pigment("cerulean").colour

    def test_a_relative_path_is_read_from_the_themes_directory(self, tmp_path: Path) -> None:
        """A `.yaml` path is relative to the file that names it."""
        write_theme(tmp_path, "mine.yaml", "colours:\n  moss: '#102030'\n")
        path = write_theme(tmp_path, "t.yaml", "palette: mine.yaml\nroute_ink:\n  colour: moss\n")
        assert Style.from_theme(path).route_ink.colour == "#102030"

    def test_a_gpl_path_works(self, tmp_path: Path) -> None:
        """A `.gpl` palette's alias is a colour in the theme."""
        write_theme(tmp_path, "mine.gpl", "GIMP Palette\n16 32 48\tMoss\n")
        path = write_theme(tmp_path, "t.yaml", "palette: mine.gpl\nroute_ink:\n  colour: moss\n")
        assert Style.from_theme(path).route_ink.colour == "#102030"

    def test_an_unknown_name_is_located_with_the_suggestion(self, tmp_path: Path) -> None:
        """`palette: plan` is a located error at the key."""
        path = write_theme(tmp_path, "t.yaml", "palette: plan\n")
        assert _problems(path) == [
            (path, 1, "no palette named 'plan'; did you mean plain?; available: plain")
        ]

    def test_a_missing_file_is_located_at_the_key(self, tmp_path: Path) -> None:
        """`palette: gone.yaml` is a problem of the theme at the `palette:` line."""
        path = write_theme(tmp_path, "t.yaml", "route_ink: {}\npalette: gone.yaml\n")
        assert _problems(path) == [(path, 2, f"no such palette file: {tmp_path / 'gone.yaml'}")]

    def test_a_palette_with_a_bad_row_reports_the_palette_file(self, tmp_path: Path) -> None:
        """The problem is the palette file's, at its own line, and the theme's `palette:` line is named."""
        palette = write_theme(tmp_path, "mine.gpl", "GIMP Palette\n0 0 0\n")
        path = write_theme(tmp_path, "t.yaml", "palette: mine.gpl\n")
        found = {(p, line) for p, line, _ in _problems(path)}
        assert found == {(palette, 2), (path, 1)}

    def test_a_palette_that_is_no_string_is_refused(self, tmp_path: Path) -> None:
        """`palette: 5` is refused."""
        path = write_theme(tmp_path, "t.yaml", "palette: 5\n")
        assert _problems(path) == [(path, 1, "is a palette name or a .yaml or .gpl path")]

    def test_the_nearest_palette_is_the_one_in_effect(self, tmp_path: Path) -> None:
        """A child's `palette:` takes the parent's palette aliases out of scope."""
        write_theme(tmp_path, "mine.yaml", "colours:\n  moss: '#102030'\n")
        write_theme(tmp_path, "parent.yaml", "palette: plain\n")
        path = write_theme(
            tmp_path,
            "t.yaml",
            "extends: parent.yaml\npalette: mine.yaml\nroute_ink:\n  colour: sky\n",
        )
        (problem,) = _problems(path)
        assert problem[1] == 4

    def test_a_palette_alias_that_is_a_theme_pigment_is_refused(self, tmp_path: Path) -> None:
        """A palette alias equal to a pigment the theme defines clashes."""
        text = "pigments:\n  sky: {colour: '#000000'}\npalette: plain\n"
        path = write_theme(tmp_path, "t.yaml", text)
        assert _problems(path) == [(path, 3, "palette alias 'sky' is a pigment name of the theme")]
