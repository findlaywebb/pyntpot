"""Reference pages gate: each page names every fact the code it describes holds.

The facts are read from the code, never from rendered help or a copy of a table: the CLI
parser's actions, the style groups' dataclass fields, the keys the cache and the manifest
write, `PIGMENTS` and the brush tables. A page that omits one fails here, so the reference
cannot fall behind the code.
"""

import argparse
import dataclasses
import runpy
from pathlib import Path

import pytest

from pyntpot.ink import PIGMENTS
from pyntpot.ink.brush import BRUSH_COLOURS, BRUSH_TREATMENTS
from pyntpot.maps.cache import Cache
from pyntpot.maps.cli import build_parser
from pyntpot.maps.plates import Manifest
from pyntpot.maps.style import Style
from pyntpot.maps.style_groups import CONSUMER_ONLY, RouteInk

from support import REPO_ROOT

REFERENCE = REPO_ROOT / "docs" / "reference"
EXAMPLES = REPO_ROOT / "examples"
LYNMOUTH_MANIFEST = REPO_ROOT / "tests" / "golden" / "lynmouth" / "plates.json"


def _page(name: str) -> str:
    """Return one reference page's text, or the empty string when it is not written."""
    path = REFERENCE / name
    return path.read_text() if path.is_file() else ""


def _parsers(parser: argparse.ArgumentParser) -> list[argparse.ArgumentParser]:
    """Return a parser and every subcommand parser under it."""
    found = [parser]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub in action.choices.values():
                found.extend(_parsers(sub))
    return found


def _cli_facts() -> list[str]:
    """Return every option string, positional name, subcommand name and help text of the parser."""
    facts: list[str] = []
    for parser in _parsers(build_parser()):
        for action in parser._actions:
            facts.extend(action.option_strings or [action.dest])
            if action.help:
                facts.append(action.help)
            if isinstance(action, argparse._SubParsersAction):
                facts.extend(action.choices)
                facts.extend(choice.help for choice in action._choices_actions if choice.help)
    return facts


def _style_fields() -> dict[str, list[str]]:
    """Return the field names of each style group, by group name, route inks included."""
    groups: dict[str, list[str]] = {}
    for name, info in Style.model_fields.items():
        assert dataclasses.is_dataclass(info.annotation)
        groups[name] = [spec.name for spec in dataclasses.fields(info.annotation)]
    groups["route_inks.<sport>"] = [spec.name for spec in dataclasses.fields(RouteInk)]
    return groups


def _manifest_keys() -> list[str]:
    """Return every key `plates.json` is written with, the dark grid's included."""
    record = Manifest.from_json(LYNMOUTH_MANIFEST.read_text()).to_dict()
    return [*record, *record["dark"]]


class TestEveryPageExists:
    """The six reference pages and the glossary pointer are written."""

    @pytest.mark.parametrize(
        "name",
        [
            "cli.md",
            "style-fields.md",
            "cache-layout.md",
            "manifest.md",
            "pigments.md",
            "brushes.md",
            "glossary.md",
        ],
    )
    def test_page_is_written(self, name):
        """Each reference page exists and is not empty."""
        assert _page(name).strip(), f"docs/reference/{name} is missing or empty"

    def test_glossary_page_points_to_the_glossary(self):
        """The glossary page links to GLOSSARY.md at the repo root."""
        assert "../../GLOSSARY.md" in _page("glossary.md")


class TestCli:
    """The command line page names every option and help text the parser holds."""

    def test_page_names_every_option_and_help_text(self):
        """Every option string, positional, subcommand and help text of the parser is in cli.md."""
        text = _page("cli.md")
        missing = [fact for fact in _cli_facts() if fact not in text]
        assert not missing, f"cli.md lacks: {missing}"


class TestStyleFields:
    """The style fields page names every field of every style group."""

    def test_every_field_of_every_group_is_named(self):
        """Each dataclass field of each style group appears in style-fields.md as code."""
        text = _page("style-fields.md")
        missing = [
            f"{group}.{name}"
            for group, names in _style_fields().items()
            for name in names
            if f"`{name}`" not in text
        ]
        assert not missing, f"style-fields.md lacks: {missing}"

    def test_every_group_has_a_heading(self):
        """Each style group is a section of style-fields.md headed with its table name."""
        text = _page("style-fields.md")
        missing = [group for group in Style.model_fields if f"## `{group}`" not in text]
        assert not missing, f"style-fields.md lacks a section for: {missing}"

    def test_consumer_only_fields_are_named(self):
        """The painter fields that belong to no group are named in style-fields.md."""
        text = _page("style-fields.md")
        missing = [name for name in CONSUMER_ONLY if f"`{name}`" not in text]
        assert not missing, f"style-fields.md lacks: {missing}"


class TestCacheLayout:
    """The cache page names every file and directory the cache and the plates write."""

    def test_payload_files_and_plates_directory_are_named(self):
        """Each payload file pattern, the plates directory and plates.json are in cache-layout.md."""
        text = _page("cache-layout.md")
        cache = Cache(Path("cache"))
        names = [
            cache.features_path("<key>").name,
            cache.landcover_path("<key>").name,
            cache.elevation_path("<key>").name,
            cache.plates_dir("<key>").relative_to("cache").as_posix(),
            "plates.json",
        ]
        missing = [name for name in names if f"`{name}`" not in text]
        assert not missing, f"cache-layout.md lacks: {missing}"

    def test_plate_files_come_from_the_manifest(self):
        """Each plate file a painted map holds is named in cache-layout.md."""
        text = _page("cache-layout.md")
        files = Manifest.from_json(LYNMOUTH_MANIFEST.read_text()).files.values()
        missing = [name for name in files if f"`{name}`" not in text]
        assert not missing, f"cache-layout.md lacks: {missing}"

    def test_label_plate_files_and_sidecar_keys_are_named(self):
        """Both label plates, their sidecars and the sidecar's keys are in cache-layout.md."""
        text = _page("cache-layout.md")
        facts = [
            f"labels-{route}.{suffix}"
            for route in ("centreline", "outline")
            for suffix in ("webp", "json")
        ]
        facts += ["key", "face", "route"]
        missing = [fact for fact in facts if f"`{fact}`" not in text]
        assert not missing, f"cache-layout.md lacks: {missing}"

    def test_key_inputs_are_named(self):
        """The four inputs the payload key hashes are in cache-layout.md."""
        text = _page("cache-layout.md")
        missing = [
            name for name in ("box", "margin_m", "features", "elevation") if f"`{name}`" not in text
        ]
        assert not missing, f"cache-layout.md lacks: {missing}"


class TestManifest:
    """The manifest page names every key `plates.json` is written with."""

    def test_every_key_is_named(self):
        """Each top-level key of plates.json and each key of its dark grid is in manifest.md."""
        text = _page("manifest.md")
        missing = [key for key in _manifest_keys() if f"`{key}`" not in text]
        assert not missing, f"manifest.md lacks: {missing}"


class TestPigments:
    """The pigments page names every pigment key."""

    def test_every_key_is_named(self):
        """Each key of PIGMENTS is in pigments.md as code."""
        text = _page("pigments.md")
        missing = [key for key in PIGMENTS if f"`{key}`" not in text]
        assert not missing, f"pigments.md lacks: {missing}"


class TestBrushes:
    """The brushes page names every brush id, and the sheet script lists the same ids."""

    @staticmethod
    def _table_ids() -> set[str]:
        """Return every id the private brush tables make: prefix, row, hyphen, column."""
        return {
            f"{prefix}{row}-{column}"
            for prefix, columns in BRUSH_COLOURS.items()
            for column in columns
            for row in BRUSH_TREATMENTS
        }

    def test_sheet_script_lists_exactly_the_table_ids(self):
        """The literal tuple in examples/brush_sheet.py equals the ids the brush tables make."""
        script = EXAMPLES / "brush_sheet.py"
        listed = runpy.run_path(str(script))["BRUSH_IDS"] if script.is_file() else ()
        assert len(listed) == len(set(listed)), "brush_sheet.py lists an id twice"
        assert set(listed) == self._table_ids()

    def test_every_id_is_named(self):
        """Each brush id is in brushes.md as code."""
        text = _page("brushes.md")
        missing = sorted(brush for brush in self._table_ids() if f"`{brush}`" not in text)
        assert not missing, f"brushes.md lacks: {missing}"
