"""`resolve`: a theme named or given by its file, its `extends` chain, and every problem in it."""

import dataclasses
from pathlib import Path

import pytest

from pyntpot.maps.style import Style
from pyntpot.maps.theme_errors import ThemeError
from pyntpot.maps.theme_resolve import NAME, names_in, resolve, theme_names

#: Each style group's dataclass, by its key, built as `style.py` builds it.
GROUPS: dict[str, type] = {
    name: info.annotation
    for name, info in Style.model_fields.items()
    if isinstance(info.annotation, type)
}


def _base() -> dict[str, object]:
    """The default table, one entry per group, built as `style.py` builds it."""
    return {name: dataclasses.asdict(getattr(Style(), name)) for name in Style.model_fields}


def _resolve(theme: str | Path, relative_to: Path) -> dict[str, object]:
    """Resolve `theme` from `relative_to` against the real groups and defaults."""
    return resolve(theme, relative_to=relative_to, groups=GROUPS, base=_base())


def _write(root: Path, name: str, text: str) -> Path:
    """Write `text` to `root / name`, making its directories."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _refusal(theme: str | Path, relative_to: Path) -> ThemeError:
    """The `ThemeError` resolving `theme` raises."""
    with pytest.raises(ThemeError) as caught:
        _resolve(theme, relative_to)
    return caught.value


def _group(table: dict[str, object], name: str) -> dict[str, object]:
    """The group `name` of a resolved table, as a dict."""
    group = table[name]
    assert isinstance(group, dict)
    return {str(key): value for key, value in group.items()}


class TestTheRuleForATheme:
    """How a name or a path picks a theme, in the rule's order."""

    def test_a_yaml_path_is_read_relative_to_the_caller(self, tmp_path: Path) -> None:
        """A `.yaml` path is read from `relative_to`, as a `str` or a `Path`."""
        _write(tmp_path, "t.yaml", "card:\n  display_px: 120\n")
        for theme in ("t.yaml", Path("t.yaml")):
            assert _group(_resolve(theme, tmp_path), "card")["display_px"] == 120

    def test_an_absolute_yaml_path_ignores_relative_to(self, tmp_path: Path) -> None:
        """An absolute `.yaml` path is read where it is."""
        path = _write(tmp_path, "t.yaml", "card:\n  display_px: 120\n")
        assert _group(_resolve(path, tmp_path / "elsewhere"), "card")["display_px"] == 120

    @pytest.mark.parametrize("theme", ["old.yml", Path("old.yml")], ids=["str", "path"])
    def test_a_yml_theme_is_refused_with_the_yaml_name(
        self, tmp_path: Path, theme: str | Path
    ) -> None:
        """A `.yml` theme is refused with the `.yaml` name it should have."""
        error = _refusal(theme, tmp_path)
        (problem,) = error.problems
        assert problem.message == "theme files end in .yaml; did you mean 'old.yaml'?"
        assert (problem.path, problem.key, problem.line) == (Path("old.yml"), "", None)

    @pytest.mark.parametrize("theme", ["old.toml", Path("old.toml")], ids=["str", "path"])
    def test_a_toml_theme_is_refused_with_the_conversion_pointer(
        self, tmp_path: Path, theme: str | Path
    ) -> None:
        """A `.toml` theme, named as a `str` or a `Path`, points at the conversion how-to."""
        (problem,) = _refusal(theme, tmp_path).problems
        assert problem.message == (
            "themes are YAML since ADR 0069: see 'Convert a TOML theme' in the theme how-to"
        )
        assert (problem.path, problem.key, problem.line) == (Path("old.toml"), "", None)

    @pytest.mark.parametrize("theme", [Path("sepia"), Path("t.json")], ids=["bare", "json"])
    def test_a_path_is_never_a_name(self, tmp_path: Path, theme: Path) -> None:
        """A `Path` that does not end in `.yaml` is refused, even when it spells a name."""
        (problem,) = _refusal(theme, tmp_path).problems
        assert problem.message == "a theme file ends in .yaml"

    def test_the_default_name_is_the_base(self, tmp_path: Path) -> None:
        """`default` resolves to the base table itself, reading no file."""
        assert _resolve("default", tmp_path) == _base()

    def test_an_unknown_name_is_refused_with_the_names(self, tmp_path: Path) -> None:
        """A well-formed name that is not packaged is refused, listing the names there are."""
        (problem,) = _refusal("sepia-two", tmp_path).problems
        names = ", ".join(theme_names())
        assert problem.message == f"no theme named 'sepia-two'; available: {names}"
        assert (problem.path, problem.key, problem.line) == (Path("sepia-two"), "", None)

    @pytest.mark.parametrize(
        "theme",
        ["Sepia", "sepia_2", "2sepia", "themes/sepia"],
        ids=["upper", "under", "digit", "dir"],
    )
    def test_neither_a_name_nor_a_path_is_refused(self, tmp_path: Path, theme: str) -> None:
        """A `str` that is no name and no `.yaml` path is refused, listing the names."""
        (problem,) = _refusal(theme, tmp_path).problems
        names = ", ".join(theme_names())
        assert problem.message == (
            f"'{theme}' is neither a theme name nor a .yaml path; available: {names}"
        )

    def test_a_name_must_match_whole(self) -> None:
        """`NAME` matches a whole name and not a name's prefix."""
        assert NAME.fullmatch("pen-and-ink") is not None
        assert NAME.fullmatch("sepia_2") is None

    def test_a_missing_file_is_refused(self, tmp_path: Path) -> None:
        """A `.yaml` path naming no file is refused, as the file as a whole."""
        (problem,) = _refusal("absent.yaml", tmp_path).problems
        assert problem.message == "no such theme file"
        assert (problem.path, problem.key, problem.line) == (tmp_path / "absent.yaml", "", None)


class TestTheChain:
    """How `extends` chains themes, base first."""

    def test_a_three_file_chain_applies_in_order(self, tmp_path: Path) -> None:
        """`c` extends `b` extends `a`: each later file wins, and every earlier key not overridden stays."""
        _write(tmp_path, "a.yaml", "card:\n  display_px: 100\n  supersample: 3\n")
        _write(tmp_path, "b.yaml", "extends: a.yaml\ncard:\n  display_px: 200\n")
        _write(tmp_path, "c.yaml", "extends: b.yaml\nwash:\n  blooms: false\n")
        table = _resolve("c.yaml", tmp_path)
        assert (_group(table, "card")["display_px"], _group(table, "card")["supersample"]) == (
            200,
            3,
        )
        assert _group(table, "wash")["blooms"] is False
        assert "extends" not in table

    def test_a_relative_extends_is_read_from_the_extending_file(self, tmp_path: Path) -> None:
        """`extends: ../shared/base.yaml` is found from the extending file's directory."""
        _write(tmp_path, "shared/base.yaml", "card:\n  display_px: 300\n")
        _write(tmp_path, "themes/t.yaml", "extends: ../shared/base.yaml\n")
        assert _group(_resolve("themes/t.yaml", tmp_path), "card")["display_px"] == 300

    def test_a_two_file_cycle_is_refused(self, tmp_path: Path) -> None:
        """`a` extending `b` extending `a` is refused on the closing `extends` line."""
        _write(tmp_path, "a.yaml", "extends: b.yaml\n")
        _write(tmp_path, "b.yaml", "card:\n  display_px: 120\nextends: a.yaml\n")
        (problem,) = _refusal("a.yaml", tmp_path).problems
        assert problem.message == "extends cycle: a.yaml -> b.yaml -> a.yaml"
        assert (problem.path, problem.key, problem.line) == (tmp_path / "b.yaml", "extends", 3)

    def test_a_self_cycle_is_refused(self, tmp_path: Path) -> None:
        """A theme extending itself is refused."""
        _write(tmp_path, "a.yaml", "extends: a.yaml\n")
        (problem,) = _refusal("a.yaml", tmp_path).problems
        assert problem.message == "extends cycle: a.yaml -> a.yaml"

    def test_problems_in_two_files_are_both_reported(self, tmp_path: Path) -> None:
        """A problem in a theme and another in the theme it extends are reported together."""
        _write(tmp_path, "a.yaml", "wash:\n  blom: true\n")
        _write(tmp_path, "b.yaml", "extends: a.yaml\ncard:\n  display_px: '5'\n")
        error = _refusal("b.yaml", tmp_path)
        assert [(problem.path.name, problem.key) for problem in error.problems] == [
            ("a.yaml", "wash.blom"),
            ("b.yaml", "card.display_px"),
        ]

    def test_a_read_problem_is_reported_once(self, tmp_path: Path) -> None:
        """A problem the reader finds is reported once, and the file is not checked as well."""
        _write(tmp_path, "t.yaml", "a: &x 1\n")
        assert len(_refusal("t.yaml", tmp_path).problems) == 1

    def test_a_refused_extends_is_located_at_its_line(self, tmp_path: Path) -> None:
        """A chained `.toml` theme is refused under the `extends` key, at its line."""
        _write(tmp_path, "t.yaml", "card:\n  display_px: 120\nextends: old.toml\n")
        (problem,) = _refusal("t.yaml", tmp_path).problems
        assert (problem.path, problem.key, problem.line) == (Path("old.toml"), "extends", 3)

    def test_a_missing_extends_means_default(self, tmp_path: Path) -> None:
        """A theme with no `extends` overrides the base itself."""
        _write(tmp_path, "t.yaml", "card:\n  display_px: 120\n")
        table = _resolve("t.yaml", tmp_path)
        assert _group(table, "card")["display_px"] == 120
        assert _group(table, "wash") == _group(_base(), "wash")

    def test_extends_default_overrides_the_base(self, tmp_path: Path) -> None:
        """`extends: default` overrides the base, each leaf converted to its field's type."""
        _write(tmp_path, "t.yaml", "extends: default\ncard:\n  display_px: 120\n")
        assert _group(_resolve("t.yaml", tmp_path), "card")["display_px"] == 120
        _write(tmp_path, "w.yaml", "extends: default\nwash:\n  wet_bleed_px: 20\n")
        bleed = _group(_resolve("w.yaml", tmp_path), "wash")["wet_bleed_px"]
        assert (bleed, type(bleed)) == (20.0, float)


class TestNames:
    """The theme names a directory holds."""

    def test_an_absent_directory_holds_only_the_default(self, tmp_path: Path) -> None:
        """A directory that is not there names only `default`."""
        assert names_in(tmp_path / "absent") == ("default",)

    def test_a_directory_names_its_yaml_stems_and_the_default(self, tmp_path: Path) -> None:
        """Each `.yaml` file's stem is a name, with `default`, sorted; the schema is not."""
        for name in ("b.yaml", "a.yaml", "theme.schema.json"):
            _write(tmp_path, name, "")
        assert names_in(tmp_path) == ("a", "b", "default")

    def test_the_packaged_names_include_the_default(self) -> None:
        """The package's themes include `default`."""
        assert "default" in theme_names()
