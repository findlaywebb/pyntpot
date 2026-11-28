"""Every theme paints the preview card, and each card has the pinned size, mean colour and labels."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from pyntpot.maps import OpenTopoData, OverpassFeatures, Style

from support import REPO_ROOT
from support.examples import load_example

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"

#: The card's size in pixels, width then height, which no theme changes.
CARD_SIZE = (1200, 1071)

#: Each theme's mean red, green and blue over the whole card, pinned from a paint. A packaged
#: theme is keyed by its name, an example theme by its path relative to the repository's top directory.
MEAN_RGB: dict[str, tuple[float, float, float]] = {
    "bold": (194.3, 209.0, 202.8),
    "default": (209.7, 206.5, 190.4),
    "pen-and-ink": (221.8, 217.9, 207.0),
    "sepia": (198.3, 169.1, 119.3),
    "winter": (201.8, 213.5, 222.6),
    "examples/themes/ambleside-cased.yaml": (171.2, 172.6, 154.1),
    "examples/themes/ambleside-hero.yaml": (181.1, 183.0, 165.3),
    "examples/themes/ambleside.yaml": (171.3, 172.7, 154.1),
    "examples/themes/oxford.yaml": (188.7, 188.0, 169.0),
    "examples/themes/skye.yaml": (165.1, 158.1, 131.3),
    "examples/themes/y-fenni.yaml": (196.2, 183.1, 156.4),
    "examples/themes/yr-wyddfa.yaml": (140.1, 146.0, 150.0),
}

#: The distinct names each theme letters on the card, pinned from a paint.
LABELS: dict[str, frozenset[str]] = {
    "bold": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "default": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "pen-and-ink": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "sepia": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "winter": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/ambleside-cased.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/ambleside-hero.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/ambleside.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/oxford.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/skye.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
    "examples/themes/y-fenni.yaml": frozenset(
        {
            "East Lyn River",
            "Foreland Point",
            "High tide at Lynmouth",
            "Lynton",
            "finish",
            "start",
            "Lynmouth",
        }
    ),
    "examples/themes/yr-wyddfa.yaml": frozenset(
        {"East Lyn River", "Foreland Point", "High tide at Lynmouth", "Lynton", "finish", "start"}
    ),
}

#: How far a channel's mean may move between operating systems, out of 255.
MEAN_TOLERANCE = 1.5


def test_the_pinned_themes_are_every_packaged_and_example_theme() -> None:
    """The golden table has one entry for each packaged theme and each example theme file."""
    examples = {
        f"examples/themes/{p.name}" for p in (REPO_ROOT / "examples" / "themes").glob("*.yaml")
    }
    assert set(MEAN_RGB) == set(Style.themes()) | examples
    assert set(LABELS) == set(MEAN_RGB)


@pytest.mark.golden
@pytest.mark.parametrize("theme", list(MEAN_RGB), ids=[Path(t).stem for t in MEAN_RGB])
def test_the_theme_paints_the_preview_card(tmp_path: Path, theme: str) -> None:
    """From the fixture's cache alone, the theme paints a card of the pinned size, mean colour and labels."""
    cache = tmp_path / "cache"
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "preview", cache)
    example = load_example("theme_preview", "example_theme_preview")

    card, lettering = example["preview"](
        Style.from_theme(theme, relative_to=REPO_ROOT),
        track=cache / "track.gpx",
        cache_dir=cache,
        features=OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0),
        elevation=OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0),
    )

    assert card.mode == "RGB"
    assert card.size == CARD_SIZE
    mean = np.asarray(card).reshape(-1, 3).mean(axis=0)
    assert mean == pytest.approx(MEAN_RGB[theme], abs=MEAN_TOLERANCE)
    assert {label.name for label in lettering.labels} == LABELS[theme]
