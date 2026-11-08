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

from support import REPO_ROOT


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


def test_no_package_file_restates_the_defaults():
    """No file under `src/pyntpot/` restates the model's defaults."""
    assert files_that_restate_the_defaults(REPO_ROOT / "src" / "pyntpot") == []


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
