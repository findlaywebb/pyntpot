"""The fixture key and the fixture, golden and smoke-plate directories, the only source of each.

Imports only `pathlib`, never the package, so `conftest.py` can read it in sessions
that must not load `pyntpot`, such as the architecture tests.
"""

from pathlib import Path

_TESTS = Path(__file__).resolve().parents[1]

#: The cache key of the Lynmouth track with the shipped providers' ids, which names the
#: fixture's payload files.
KEY: str = "f173b2f7a20bb9d4"

#: The Lynmouth fixture: track and cached provider payloads.
FIXTURE_DIR: Path = _TESTS / "fixtures" / "lynmouth"

#: The cache keys of the focus-place fixtures with the shipped providers' ids, which name
#: each fixture's payload files. Each directory beside the Lynmouth one is `FIXTURES / <name>`.
KESWICK_KEY: str = "f2f4692b66d96eb9"
TROTTERNISH_KEY: str = "70696067aa04a7f8"
YR_WYDDFA_KEY: str = "353c7a77ae84f4c1"
OXFORD_KEY: str = "edf326cc49d5cc52"
Y_FENNI_KEY: str = "31d229011257f9fa"
AMBLESIDE_KEY: str = "f0a137ce97afcb43"
SKYE_KEY: str = "ada01f635902a1fd"

#: The directory holding every fixture, Lynmouth's included.
FIXTURES: Path = _TESTS / "fixtures"

#: The committed golden outputs for the Lynmouth fixture.
GOLDEN_DIR: Path = _TESTS / "golden" / "lynmouth"

#: The smoke box's approved wash plate, the bytes `SMOKE_SHA["wash"]` in the painter's smoke test pins.
SMOKE_DIR: Path = _TESTS / "golden" / "smoke"
