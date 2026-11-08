"""The model is the one source of defaults: every field has one, and no package file restates them.

A style group's dataclass defaults are the default look (ADR 0069), so every field of
every group, nested dataclass fields included, has a default, every `Style` field has
one, `Style()` is the default look, and no file under `src/pyntpot/` holds a second copy
of the defaults: no TOML file, no `default.*` file, and nothing among the packaged themes
but YAML themes and the schema.

Each check is a plain function returning the problems it finds as sorted strings, empty
when the rule holds. The real-tree tests hold the real model and the real package to it;
the self-tests plant each defect, in planted classes and in `tmp_path`, and show the
check reporting it. Nothing here writes under the repository.
"""

import dataclasses
import typing
from collections.abc import Mapping
from pathlib import Path

import pydantic

from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.maps import Style
from pyntpot.maps.style import _base, _groups
from pyntpot.maps.style_groups import CoverStyle
from pyntpot.maps.theme_check import EXTENDS, check_theme
from pyntpot.maps.theme_errors import ThemeError
from pyntpot.maps.theme_read import read_theme
from pyntpot.maps.theme_resolve import resolve

from support import REPO_ROOT

#: Where theme files live: the packaged themes and the example themes.
THEME_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "src" / "pyntpot" / "maps" / "themes",
    REPO_ROOT / "examples" / "themes",
)


def fields_without_a_default(groups: Mapping[str, type]) -> list[str]:
    """Name every dataclass field with no default, walking fields that are dataclasses."""
    found: list[str] = []
    for name, group in groups.items():
        found.extend(_group_fields_without_a_default(group, name))
    return sorted(found)


def _group_fields_without_a_default(group: type, where: str) -> list[str]:
    """Name `group`'s fields with no default as `where.field`, recursing into dataclass fields."""
    if not dataclasses.is_dataclass(group):
        return []
    hints = typing.get_type_hints(group)
    found: list[str] = []
    for spec in dataclasses.fields(group):
        if spec.default is dataclasses.MISSING and spec.default_factory is dataclasses.MISSING:
            found.append(f"{where}.{spec.name}")
        hint = hints.get(spec.name)
        if isinstance(hint, type):
            found.extend(_group_fields_without_a_default(hint, f"{where}.{spec.name}"))
    return found


def required_style_fields(model: type[pydantic.BaseModel]) -> list[str]:
    """Name every field of `model` that has no default."""
    return sorted(name for name, info in model.model_fields.items() if info.is_required())


def files_that_restate_the_defaults(package: Path) -> list[str]:
    """Name every file under `package` that could hold a second copy of the defaults."""
    found = {*package.rglob("*.toml"), *package.rglob("default.*")}
    themes = package / "maps" / "themes"
    if themes.is_dir():
        found.update(
            path
            for path in themes.iterdir()
            if path.suffix != ".yaml" and path.name != "theme.schema.json"
        )
    return sorted({path.relative_to(package).as_posix() for path in found})


def theme_files() -> list[Path]:
    """Every YAML theme file among the packaged themes and the example themes, sorted."""
    return sorted(path for directory in THEME_DIRS for path in directory.glob("*.yaml"))


def keys_set_to_their_base_value(theme: Path) -> list[str]:
    """Name every key `theme` sets to the value the theme it extends already has.

    A theme that does not load is reported as `{file name}: does not load: {problem}`, one
    entry per problem; otherwise each restated leaf as `{file name}: {dotted key path}`.
    """
    try:
        resolve(theme, relative_to=theme.parent, groups=_groups(), base=_base())
    except ThemeError as exc:
        return [f"{theme.name}: does not load: {problem}" for problem in exc.problems]
    table, _ = check_theme(read_theme(theme, theme.read_text(encoding="utf-8")), _groups())
    extends = table.get(EXTENDS, "default")
    assert isinstance(extends, str)
    below = resolve(extends, relative_to=theme.parent, groups=_groups(), base=_base())
    sets = {key: value for key, value in table.items() if key != EXTENDS}
    return sorted(f"{theme.name}: {'.'.join(path)}" for path in _restated(sets, below, ()))


def _restated(
    table: Mapping[str, object], below: Mapping[str, object], where: tuple[str, ...]
) -> list[tuple[str, ...]]:
    """The key path of every leaf of `table` equal to the leaf of `below` at the same path."""
    found: list[tuple[str, ...]] = []
    for key, value in table.items():
        under = below.get(key)
        if isinstance(value, Mapping) and isinstance(under, Mapping):
            found.extend(_restated(value, under, (*where, key)))
        elif value == under:
            found.append((*where, key))
    return found


@dataclasses.dataclass(frozen=True, kw_only=True)
class _NoDefault:
    """A planted group with one field lacking a default."""

    blooms: bool
    flow_rim: bool = True


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Outer:
    """A planted group whose nested group has a field lacking a default."""

    inner: _NoDefault = dataclasses.field(default_factory=lambda: _NoDefault(blooms=True))


class _RequiredStyle(pydantic.BaseModel):
    """A planted model with one field lacking a default."""

    paper: PaperStyle
    wash: WashStyle = pydantic.Field(default_factory=WashStyle)


def _write(root: Path, *names: str) -> None:
    """Write an empty file at each relative name under `root`."""
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")


def test_every_style_group_field_has_a_default():
    """Every field of every style group, and every `Style` field, has a default."""
    groups = {
        name: info.annotation
        for name, info in Style.model_fields.items()
        if isinstance(info.annotation, type)
    }
    assert groups.keys() == Style.model_fields.keys()
    assert fields_without_a_default(groups) == []
    assert required_style_fields(Style) == []


def test_the_default_theme_is_the_model_with_nothing_overridden():
    """`Style()` with nothing overridden is the default look."""
    assert Style() == Style.default()
    assert Style() == Style.named("default")


def test_no_package_file_restates_the_defaults():
    """No file under `src/pyntpot/` restates the model's defaults."""
    assert files_that_restate_the_defaults(REPO_ROOT / "src" / "pyntpot") == []


def test_no_theme_file_sets_a_key_to_its_base_value():
    """No packaged or example theme loads badly or restates a value of the theme it extends."""
    found = [entry for theme in theme_files() for entry in keys_set_to_their_base_value(theme)]
    assert "\n".join(found) == ""


def test_the_theme_file_checks_see_every_theme():
    """The theme-file checks find all ten themes, so none is skipped by a wrong directory."""
    assert len(theme_files()) == 10


class TestTheChecksFindAPlantedDefect:
    """Each check reports the defect planted for it, and nothing in a clean tree."""

    def test_a_field_with_no_default_is_found(self):
        """A group field with no default is named, directly and inside a nested group."""
        assert fields_without_a_default({"wash": _NoDefault}) == ["wash.blooms"]
        assert fields_without_a_default({"wash": _Outer}) == ["wash.inner.blooms"]

    def test_a_required_style_field_is_found(self):
        """A model field with no default is named."""
        assert required_style_fields(_RequiredStyle) == ["paper"]

    def test_a_default_theme_file_is_found(self, tmp_path):
        """A default theme among the packaged themes is reported."""
        _write(tmp_path, "maps/themes/default.yaml")
        assert files_that_restate_the_defaults(tmp_path) == ["maps/themes/default.yaml"]

    def test_a_toml_file_anywhere_is_found(self, tmp_path):
        """A TOML file anywhere in the package is reported."""
        _write(tmp_path, "ink/old.toml")
        assert files_that_restate_the_defaults(tmp_path) == ["ink/old.toml"]

    def test_a_default_file_outside_the_themes_is_found(self, tmp_path):
        """A `default.*` file outside the themes is reported."""
        _write(tmp_path, "ink/default.json")
        assert files_that_restate_the_defaults(tmp_path) == ["ink/default.json"]

    def test_a_stray_file_among_the_themes_is_found(self, tmp_path):
        """A file among the themes that is neither a YAML theme nor the schema is reported."""
        _write(tmp_path, "maps/themes/notes.txt")
        assert files_that_restate_the_defaults(tmp_path) == ["maps/themes/notes.txt"]

    def test_a_clean_package_has_nothing_to_report(self, tmp_path):
        """A package with only YAML themes, the schema and code, or no themes at all, is clean."""
        bare = tmp_path / "bare"
        _write(bare, "maps/style.py")
        assert files_that_restate_the_defaults(bare) == []
        themed = tmp_path / "themed"
        _write(themed, "maps/themes/sepia.yaml", "maps/themes/theme.schema.json", "maps/style.py")
        assert files_that_restate_the_defaults(themed) == []

    def test_a_theme_restating_a_default_is_found(self, tmp_path):
        """A theme setting a key to its default is reported; setting it to another value is not."""
        theme = tmp_path / "t.yaml"
        theme.write_text("wash:\n  blooms: true\n", encoding="utf-8")
        assert keys_set_to_their_base_value(theme) == ["t.yaml: wash.blooms"]
        theme.write_text("wash:\n  blooms: false\n", encoding="utf-8")
        assert keys_set_to_their_base_value(theme) == []

    def test_a_restated_value_is_found_after_conversion(self, tmp_path):
        """A whole number written for a float default equal to it is reported."""
        theme = tmp_path / "t.yaml"
        theme.write_text("wash:\n  wet_bleed_px: 20\n", encoding="utf-8")
        assert keys_set_to_their_base_value(theme) == ["t.yaml: wash.wet_bleed_px"]

    def test_a_restated_dict_entry_is_found(self, tmp_path):
        """A dict-field entry set to its default is reported by its dotted path."""
        wood = CoverStyle().pigments["wood"]
        theme = tmp_path / "t.yaml"
        theme.write_text(f'cover:\n  pigments:\n    wood: "{wood}"\n', encoding="utf-8")
        assert keys_set_to_their_base_value(theme) == ["t.yaml: cover.pigments.wood"]

    def test_the_base_is_the_extended_theme(self, tmp_path):
        """A key is compared with the theme it extends, not with the default look."""
        (tmp_path / "base.yaml").write_text("wash:\n  blooms: false\n", encoding="utf-8")
        child = tmp_path / "child.yaml"
        child.write_text("extends: base.yaml\nwash:\n  blooms: false\n", encoding="utf-8")
        assert keys_set_to_their_base_value(child) == ["child.yaml: wash.blooms"]
        child.write_text("extends: base.yaml\nwash:\n  blooms: true\n", encoding="utf-8")
        assert keys_set_to_their_base_value(child) == []

    def test_a_theme_that_does_not_load_is_reported(self, tmp_path):
        """A theme that does not load is reported once per problem, as not loading."""
        theme = tmp_path / "t.yaml"
        theme.write_text("wash:\n  blom: true\n", encoding="utf-8")
        (entry,) = keys_set_to_their_base_value(theme)
        assert entry.startswith("t.yaml: does not load:")
