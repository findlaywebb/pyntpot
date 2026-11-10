"""A preset expands to the stack it names: the same style and the same digests as writing it out."""

import dataclasses
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pyntpot.ink import Casing, Colour, Glow, Shadow
from pyntpot.maps import EffectStack, Style
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, LINE_CLASSES

from support.properties import UNTIMED
from support.theme_dump import dump_theme

_NAMES = st.sampled_from(("soft", "edge", "wide_cast", "mist2"))
_PX = st.floats(0.0, 16.0, allow_nan=False)
_UNIT = st.floats(0.0, 1.0, allow_nan=False)
_HEX = st.text(alphabet="0123456789abcdef", min_size=6, max_size=6).map(lambda h: Colour(f"#{h}"))


def _written(stack: EffectStack) -> dict[str, object]:
    """The stack as a theme table: each effect by its kind, in the stack's order."""
    return {type(effect).__name__.lower(): dataclasses.asdict(effect) for effect in stack.effects}


def _load(table: dict[str, object]) -> Style:
    """The style a theme holding `table` loads to."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "t.yaml"
        path.write_text(dump_theme(table), encoding="utf-8")
        return Style.from_yaml(path)


@st.composite
def stacks(draw: st.DrawFn) -> EffectStack:
    """Draw a stack of up to one casing, one glow and one shadow, in any order, in range."""
    casing = Casing(width_px=draw(_PX), strength=draw(_UNIT), colour=draw(_HEX))
    glow = Glow(spread_px=draw(_PX), blur_px=draw(_PX), strength=draw(_UNIT))
    shadow = Shadow(offset_px=draw(_PX), blur_px=draw(_PX), strength=draw(_UNIT), colour=draw(_HEX))
    kept = draw(st.lists(st.sampled_from((casing, glow, shadow)), unique=True, max_size=3))
    return EffectStack(effects=tuple(kept))


@given(st.sampled_from(sorted(BUILT_IN_PRESETS)), st.sampled_from(sorted(LINE_CLASSES)))
@settings(UNTIMED, max_examples=30)
def test_a_built_in_preset_equals_its_written_out_stack(preset: str, line_class: str) -> None:
    """Naming a built-in preset loads to the same style and digests as writing its stack."""
    named = _load({"line_effects": {line_class: preset}})
    written = _load({"line_effects": {line_class: _written(BUILT_IN_PRESETS[preset])}})
    assert named == written
    assert (named.digest(), named.base_digest(), named.lettering_digest()) == (
        written.digest(),
        written.base_digest(),
        written.lettering_digest(),
    )


@given(_NAMES, st.sampled_from(sorted(LINE_CLASSES)), stacks())
@settings(UNTIMED, max_examples=50)
def test_a_theme_preset_equals_its_written_out_stack(
    name: str, line_class: str, stack: EffectStack
) -> None:
    """A preset a theme defines loads to the same style and digests as the stack it holds."""
    defined = {name: _written(stack)}
    named = _load({"effect_presets": defined, "line_effects": {line_class: name}})
    written = _load({"line_effects": {line_class: _written(stack)}})
    assert named == written
    assert (named.digest(), named.base_digest(), named.lettering_digest()) == (
        written.digest(),
        written.base_digest(),
        written.lettering_digest(),
    )
