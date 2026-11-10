"""Empty or off `line_effects` leave every digest of every packaged and example theme unchanged."""

import tempfile
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


@given(
    st.sampled_from(_THEMES),
    st.dictionaries(st.sampled_from(sorted(LINE_CLASSES)), _OFF, max_size=len(LINE_CLASSES)),
)
@settings(UNTIMED, max_examples=40)
def test_off_line_effects_move_no_digest(theme: Path, off: dict[str, object]) -> None:
    """A theme extending a sampled one with off stacks has the sampled theme's three digests."""
    with tempfile.TemporaryDirectory() as directory:
        child = Path(directory) / "child.yaml"
        child.write_text(dump_theme({"extends": str(theme), "line_effects": off}), encoding="utf-8")
        extended = Style.from_yaml(child)
    base = Style.from_yaml(theme)
    assert _digests(extended) == _digests(base)
    assert extended == base
