"""Reading a theme never fails in any way but `ThemeError`, whatever the text or bytes.

The text is drawn two ways: arbitrary text, and text spliced from YAML tokens, the
spellings that resolve alike and the characters a reader refuses, so the drawn files
reach past the scanner into the walk, the load and the checker. The bytes are the same
two ways, encoded, with arbitrary bytes beside them.
"""

import contextlib
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pyntpot.maps.style import Style
from pyntpot.maps.theme_errors import ThemeError
from pyntpot.maps.theme_read import read_theme

from support.properties import UNTIMED

#: Pieces of YAML a drawn file is spliced from.
_TOKENS = (
    *("\n", "  ", " ", ": ", ":", "- ", "? ", ",", "#", "\t", "'", '"', "---\n", "%YAML 1.1\n"),
    *("[", "]", "{", "}", "&a ", "*a", "!!str ", "<<", "\x00", "\x01", "\x85", "\x9f", "﻿"),
    *("null", "~", "true", "True", "no", "1", "0x1", "0b_", "1.5", ".inf", "2024-01-01"),
    *("wash", "blooms", "card", "display_px", "extends", "default", "sepia", "x.yaml"),
)
_SPLICED = st.lists(st.sampled_from(_TOKENS), max_size=40).map("".join)
_TEXT = st.one_of(st.text(max_size=200), _SPLICED)
_BYTES = st.one_of(st.binary(max_size=200), _TEXT.map(lambda text: text.encode("utf-8")))


@given(_TEXT)
@settings(UNTIMED, max_examples=300)
def test_read_theme_never_raises(text: str) -> None:
    """`read_theme` returns for any text: every problem comes back, nothing is raised."""
    read_theme(Path("t.yaml"), text)


@given(_BYTES)
@settings(UNTIMED, max_examples=150)
def test_a_theme_file_loads_or_raises_theme_error(data: bytes) -> None:
    """`Style.from_yaml` on a file of any bytes returns a style or raises `ThemeError`."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "t.yaml"
        path.write_bytes(data)
        with contextlib.suppress(ThemeError):
            Style.from_yaml(path)
