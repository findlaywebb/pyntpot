"""Reader for the line-oriented exemption files in tests/architecture/exemptions."""

from support import REPO_ROOT

EXEMPTIONS_DIR = REPO_ROOT / "tests" / "architecture" / "exemptions"


def read_exemption_lines(name: str) -> list[str]:
    """Return the entries of an exemption file, skipping blank lines and # comments."""
    lines = (EXEMPTIONS_DIR / name).read_text().splitlines()
    return [
        stripped for line in lines if (stripped := line.strip()) and not stripped.startswith("#")
    ]
