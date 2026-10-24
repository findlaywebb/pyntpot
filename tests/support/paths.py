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
YR_WYDDFA_KEY: str = "9d5b52c0487d3b95"
OXFORD_KEY: str = "60d89f40f4793100"
Y_FENNI_KEY: str = "e634bd2f1a4ded97"

#: The directory holding every fixture, Lynmouth's included.
FIXTURES: Path = _TESTS / "fixtures"

#: The committed golden outputs for the Lynmouth fixture.
GOLDEN_DIR: Path = _TESTS / "golden" / "lynmouth"

#: The smoke box's approved wash plate, the bytes `SMOKE_SHA["wash"]` in the painter's smoke test pins.
SMOKE_DIR: Path = _TESTS / "golden" / "smoke"
