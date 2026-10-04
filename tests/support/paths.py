"""The fixture key and the fixture and golden directories, the only source of each.

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

#: The committed golden outputs for the Lynmouth fixture.
GOLDEN_DIR: Path = _TESTS / "golden" / "lynmouth"
