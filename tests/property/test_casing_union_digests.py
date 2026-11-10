"""An empty `casing_unions` leaves every digest of every packaged and example theme unchanged."""

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pyntpot.maps import Style

from support import REPO_ROOT
from support.properties import UNTIMED
from support.theme_dump import dump_theme

_THEMES = sorted(
    [
        *(REPO_ROOT / "src" / "pyntpot" / "maps" / "themes").glob("*.yaml"),
        *(REPO_ROOT / "examples" / "themes").glob("*.yaml"),
    ]
)


@given(st.sampled_from(_THEMES))
@settings(UNTIMED, max_examples=len(_THEMES))
def test_an_empty_casing_unions_is_the_identity_on_every_digest(theme: Path) -> None:
    """A child writing `casing_unions: []` has its parent's three digests, and equals it."""
    with tempfile.TemporaryDirectory() as directory:
        child = Path(directory) / "child.yaml"
        child.write_text(dump_theme({"extends": str(theme), "casing_unions": []}), encoding="utf-8")
        extended = Style.from_yaml(child)
    base = Style.from_yaml(theme)
    assert extended.digest() == base.digest()
    assert extended.base_digest() == base.base_digest()
    assert extended.lettering_digest() == base.lettering_digest()
    assert extended == base
