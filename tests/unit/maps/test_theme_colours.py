"""A theme's `colours:` table: aliases bound to pigments, the override rule and the binding rule."""

from pathlib import Path

import pytest

from pyntpot.ink import pigment
from pyntpot.maps import Style, ThemeError
from pyntpot.maps.theme_scope import resolve_colour, resolve_pigment

from support.theme_files import scope_of, write_theme


def _problems(path: Path) -> list[tuple[int | None, str]]:
    """The line and message of every problem loading the theme at `path` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(path)
    return [(p.line, p.message) for p in caught.value.problems]


class TestAnAlias:
    """What an alias binds and how a colour field reads it."""

    def test_an_alias_to_a_name_binds_that_pigment(self) -> None:
        """`sky: cerulean` binds cerulean itself, transparency and Colour Index included."""
        scope = scope_of("colours:\n  sky: cerulean\n")
        assert resolve_pigment("sky", scope) == pigment("cerulean")
        assert resolve_pigment("sky", scope).transparency == pigment("cerulean").transparency

    def test_an_alias_to_a_hex_binds_the_anonymous_pigment(self) -> None:
        """`sky: "#ABCDEF"` binds `pigment("#abcdef")`."""
        assert resolve_pigment("sky", scope_of("colours:\n  sky: '#ABCDEF'\n")) == pigment(
            "#abcdef"
        )

    def test_an_alias_may_name_a_theme_pigment(self) -> None:
        """An alias to a pigment the same file defines binds that pigment."""
        text = "pigments:\n  slate: {colour: '#111111'}\ncolours:\n  ink: slate\n"
        assert resolve_colour("ink", scope_of(text)) == "#111111"

    def test_the_table_form_takes_a_colour_and_override(self) -> None:
        """`{colour: indigo}` binds like the bare form."""
        assert resolve_colour("ink", scope_of("colours:\n  ink: {colour: indigo}\n")) == "#2c3346"

    def test_an_alias_records_the_file_and_line(self) -> None:
        """The bound alias names its file and its key's line."""
        bound = scope_of("\ncolours:\n  sky: cerulean\n").aliases["sky"]
        assert (bound.path, bound.line) == (Path("t.yaml"), 3)

    def test_a_colour_field_takes_an_alias(self, tmp_path: Path) -> None:
        """A field set to an alias holds the alias's hex."""
        path = write_theme(
            tmp_path, "t.yaml", "colours:\n  sky: cerulean\nroute_ink:\n  colour: sky\n"
        )
        assert Style.from_theme(path).route_ink.colour == "#2a7ab0"


class TestRefusals:
    """Each refusal is located at its key's line."""

    def test_an_alias_to_an_alias_is_refused(self, tmp_path: Path) -> None:
        """An alias value that is itself an alias is refused."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  sky: cerulean\n  heaven: sky\n")
        assert _problems(path) == [(3, "'sky' is an alias; an alias names a pigment or a hex")]

    def test_an_alias_named_as_a_pigment_is_refused(self, tmp_path: Path) -> None:
        """An alias that is a built-in pigment name is refused."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  indigo: cerulean\n")
        assert _problems(path) == [
            (2, "'indigo' is a pigment name; an alias needs a name of its own")
        ]

    def test_an_alias_of_the_wrong_shape_is_refused(self, tmp_path: Path) -> None:
        """A capitalised alias is refused with the shape."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  Sky: cerulean\n")
        assert _problems(path) == [
            (2, "'Sky' is not an alias: lower-case words joined by single _")
        ]

    def test_an_unknown_pigment_suggests_the_nearest(self, tmp_path: Path) -> None:
        """A misspelt pigment in an alias names the nearest pigment."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  sky: ceruleen\n")
        assert _problems(path) == [
            (2, "'ceruleen' is not a pigment or a hex; did you mean cerulean?")
        ]

    def test_an_unknown_name_in_a_field_suggests_the_nearest(self, tmp_path: Path) -> None:
        """A field set to an unbound alias is a located error with the nearest alias."""
        path = write_theme(
            tmp_path, "t.yaml", "colours:\n  sky: cerulean\nroute_ink:\n  colour: skyy\n"
        )
        assert _problems(path) == [
            (4, "'skyy' is not a pigment or a colour alias; did you mean sky?")
        ]

    def test_a_table_without_a_colour_is_refused(self, tmp_path: Path) -> None:
        """An alias table with only `override` needs a colour."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  sky: {override: true}\n")
        assert _problems(path) == [(2, "needs a colour: a pigment name or a hex")]

    def test_a_non_string_colour_is_refused(self, tmp_path: Path) -> None:
        """A number is no colour."""
        path = write_theme(tmp_path, "t.yaml", "colours:\n  sky: 5\n")
        assert _problems(path) == [
            (2, "is a pigment name, a hex or a table of colour and override")
        ]


class TestInheritance:
    """Aliases accumulate up `extends`; replacing one needs `override`."""

    @pytest.mark.parametrize("palette", ["", "palette: plain\n"], ids=["no-palette", "palette"])
    def test_override_with_nothing_to_override_is_refused(
        self, tmp_path: Path, palette: str
    ) -> None:
        """`override: true` on an alias no file below or palette binds is a located error."""
        text = f"{palette}colours:\n  lake: {{colour: cerulean, override: true}}\n"
        path = write_theme(tmp_path, "t.yaml", text)
        assert _problems(path) == [
            (len(palette.splitlines()) + 2, "'lake' overrides no alias; drop override: true")
        ]

    def test_a_child_uses_its_parents_alias(self, tmp_path: Path) -> None:
        """A child field may name an alias its parent bound."""
        write_theme(tmp_path, "parent.yaml", "colours:\n  sky: cerulean\n")
        path = write_theme(tmp_path, "t.yaml", "extends: parent.yaml\nroute_ink:\n  colour: sky\n")
        assert Style.from_theme(path).route_ink.colour == "#2a7ab0"

    def test_replacing_without_override_names_the_parents_file_and_line(
        self, tmp_path: Path
    ) -> None:
        """A child that rebinds `sky` is told where the parent bound it."""
        write_theme(tmp_path, "parent.yaml", "colours:\n  sky: cerulean\n")
        path = write_theme(tmp_path, "t.yaml", "extends: parent.yaml\ncolours:\n  sky: indigo\n")
        (problem,) = _problems(path)
        assert problem[0] == 3
        assert "'sky' is already an alias" in problem[1]
        assert "parent.yaml:2" in problem[1]

    def test_replacing_with_override_is_allowed(self, tmp_path: Path) -> None:
        """`{colour: indigo, override: true}` rebinds the inherited alias."""
        write_theme(tmp_path, "parent.yaml", "colours:\n  sky: cerulean\n")
        text = "extends: parent.yaml\ncolours:\n  sky: {colour: indigo, override: true}\n"
        text += "route_ink:\n  colour: sky\n"
        assert Style.from_theme(write_theme(tmp_path, "t.yaml", text)).route_ink.colour == "#2c3346"


class TestTheBindingRule:
    """A name binds in the file that writes it, so a child's rebinding does not recolour a parent."""

    def test_a_rebound_alias_does_not_recolour_the_parents_field(self, tmp_path: Path) -> None:
        """The parent sets the field to `sky`; a child rebinding `sky` leaves cerulean's hex."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "colours:\n  sky: cerulean\nroute_ink:\n  colour: sky\n",
        )
        text = "extends: parent.yaml\ncolours:\n  sky: {colour: indigo, override: true}\n"
        style = Style.from_theme(write_theme(tmp_path, "t.yaml", text))
        assert style.route_ink.colour == pigment("cerulean").colour

    def test_the_child_sets_the_field_to_recolour_it(self, tmp_path: Path) -> None:
        """A child that sets the field itself, after rebinding, gets the new colour."""
        write_theme(
            tmp_path, "parent.yaml", "colours:\n  sky: cerulean\nroute_ink:\n  colour: sky\n"
        )
        text = (
            "extends: parent.yaml\ncolours:\n  sky: {colour: indigo, override: true}\n"
            "route_ink:\n  colour: sky\n"
        )
        style = Style.from_theme(write_theme(tmp_path, "t.yaml", text))
        assert style.route_ink.colour == pigment("indigo").colour

    def test_a_palette_over_an_inherited_alias_fails_at_the_palette_line(
        self, tmp_path: Path
    ) -> None:
        """A child choosing `plain` over a parent's `sky` alias is an error at `palette:`."""
        write_theme(tmp_path, "parent.yaml", "colours:\n  sky: indigo\n")
        path = write_theme(tmp_path, "t.yaml", "extends: parent.yaml\npalette: plain\n")
        (problem,) = _problems(path)
        assert problem[0] == 2
        assert "palette alias 'sky' is also an alias in" in problem[1]
        assert "parent.yaml:2" in problem[1]

    def test_the_same_file_may_rebind_the_clashing_alias_with_override(
        self, tmp_path: Path
    ) -> None:
        """Rebinding every clashing alias with `override: true` clears the palette error."""
        write_theme(tmp_path, "parent.yaml", "colours:\n  sky: indigo\n")
        text = "extends: parent.yaml\npalette: plain\ncolours:\n  sky: {colour: indigo, override: true}\n"
        Style.from_theme(write_theme(tmp_path, "t.yaml", text))
