"""The fixture key and the fixture and golden directories, the only source of each.

Imports only `pathlib`, never the package, so `conftest.py` can read it in sessions
that must not load `pyntpot`, such as the architecture tests.
"""

from pathlib import Path

_TESTS = Path(__file__).resolve().parents[1]

#: The cache key the Lynmouth fixture is painted under.
KEY: str = "lynmouth"

#: The Lynmouth fixture: track and cached provider payloads.
FIXTURE_DIR: Path = _TESTS / "fixtures" / KEY

#: The committed golden outputs for the Lynmouth fixture.
GOLDEN_DIR: Path = _TESTS / "golden" / KEY
