"""Empty or off `line_effects` leave every digest of every packaged and example theme unchanged.

A child's `{}` for a class replaces the parent's stack whole, so the property draws only the
classes the sampled theme does not set: a theme that casts a class turns it off on purpose.
"""

import tempfile
from functools import cache
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pyntpot.maps import Style
from pyntpot.maps.line_effects import LINE_CLASSES

from support import REPO_ROOT
from support.properties import UNTIMED
from support.theme_dump import dump_theme

_THEMES = sorted(
    [
        *(REPO_ROOT / "src" / "pyntpot" / "maps" / "themes").glob("*.yaml"),
        *(REPO_ROOT / "examples" / "themes").glob("*.yaml"),
    ]
)

#: What a class may be given that is off: an empty stack, or a stack of effects all off.
_OFF = st.sampled_from(
    (
        {},
        {"casing": {"width_px": 0}},
        {"casing": {"width_px": -0.0}},
        {"casing": {"width_px": 2.0, "strength": 0.0}},
        {"glow": {"spread_px": 2.0, "blur_px": 2.0, "strength": 0.0}},
        {"shadow": {"offset_px": 1.0, "strength": 0.0}},
        {"reserve": {"width_px": 0}},
        {"reserve": {"width_px": 0, "pool": 0.5}},
        {"casing": {"width_px": 0.0}, "glow": {"strength": 0.0}, "shadow": {"strength": 0.0}},
    )
)


def _digests(style: Style) -> tuple[str, str, str]:
    """The style's `digest`, `base_digest` and `lettering_digest`."""
    return style.digest(), style.base_digest(), style.lettering_digest()


@cache
def _unset_classes(theme: Path) -> tuple[str, ...]:
    """The line classes the theme, with the themes it extends, sets no effect on, sorted."""
    style = Style.from_yaml(theme)
    set_here = set(style.basemap.line_effects)
    if style.route_ink.effects.effects:
        set_here.add("route")
    return tuple(sorted(LINE_CLASSES - set_here))


@st.composite
def _theme_and_off_stacks(draw: st.DrawFn) -> tuple[Path, dict[str, object]]:
    """A sampled theme and off stacks for some of the classes it sets no effect on."""
    theme = draw(st.sampled_from(_THEMES))
    free = _unset_classes(theme)
    off = draw(st.dictionaries(st.sampled_from(free), _OFF, max_size=len(free)))
    return theme, dict[str, object](off)


@given(_theme_and_off_stacks())
@settings(UNTIMED, max_examples=40)
def test_off_line_effects_move_no_digest(case: tuple[Path, dict[str, object]]) -> None:
    """A theme extending a sampled one with off stacks on classes it leaves bare has the sampled theme's three digests."""
    theme, off = case
    with tempfile.TemporaryDirectory() as directory:
        child = Path(directory) / "child.yaml"
        child.write_text(dump_theme({"extends": str(theme), "line_effects": off}), encoding="utf-8")
        extended = Style.from_yaml(child)
    base = Style.from_yaml(theme)
    assert _digests(extended) == _digests(base)
    assert extended == base
