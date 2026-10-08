"""The mutation workflow's text: the settings that keep a runaway mutant off the runner."""

from support import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "mutation.yml"


def test_every_mutmut_run_is_under_an_address_space_cap() -> None:
    """Every mutmut run in the mutation workflow runs under an address-space cap."""
    lines = [
        line for line in WORKFLOW.read_text().splitlines() if not line.lstrip().startswith("#")
    ]
    runs = [line for line in lines if "mutmut run" in line]
    assert runs
    for line in runs:
        assert "prlimit --as=" in line
        assert line.index("prlimit --as=") < line.index("uv run mutmut run")
