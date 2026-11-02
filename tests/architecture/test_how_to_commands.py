"""Every `pyntpot` command line in a how-to guide parses with the CLI's own parser.

The parser is `pyntpot.maps.cli.build_parser`, built and never run, so a guide that
misspells an option, drops a required one or names a subcommand the CLI lacks fails
here. A command line is a line of a fenced block tagged `bash`, `sh` or `shell` that starts
with `pyntpot` or `uv run pyntpot`, with any `$ ` prompt removed and lines ending in a
backslash joined to the next; a block tagged `text` shows output and is not read. It checks the arguments' shape, not that the files they name exist.
"""

import re
import shlex

import pytest

from pyntpot.maps.cli import build_parser

from support import REPO_ROOT

HOW_TO = REPO_ROOT / "docs" / "how-to"
_FENCE = re.compile(
    r"^[ \t]*(```|~~~)[ \t]*(\w*)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.DOTALL | re.MULTILINE
)
_SHELL = frozenset({"bash", "sh", "shell"})
_PROMPT = re.compile(r"^\$ ")
_PREFIXES = (("uv", "run", "pyntpot"), ("pyntpot",))


def command_lines(text: str) -> list[list[str]]:
    """Return the arguments after `pyntpot` of each command line in a Markdown text's fenced blocks."""
    found: list[list[str]] = []
    for _, tag, block in _FENCE.findall(text):
        if tag not in _SHELL:
            continue
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            words = shlex.split(_PROMPT.sub("", line.strip()), comments=True)
            for prefix in _PREFIXES:
                if tuple(words[: len(prefix)]) == prefix:
                    found.append(words[len(prefix) :])
                    break
    return found


def _guide_commands() -> list[tuple[str, list[str]]]:
    """Return every (guide name, arguments) pair under docs/how-to/."""
    return [
        (guide.name, args)
        for guide in sorted(HOW_TO.glob("*.md"))
        for args in command_lines(guide.read_text())
    ]


def _parses(args: list[str]) -> bool:
    """Return whether the CLI's parser accepts the arguments."""
    try:
        build_parser().parse_args(args)
    except SystemExit:
        return False
    return True


class TestTheGuidesCommands:
    """The commands the how-to guides show."""

    def test_the_command_line_guide_shows_commands(self) -> None:
        """The command-line guide has at least one command, so the check below cannot pass on none."""
        names = {name for name, _ in _guide_commands()}
        assert "map-from-the-command-line.md" in names

    def test_every_command_in_a_guide_parses(self, capfd: pytest.CaptureFixture[str]) -> None:
        """Each `pyntpot` command line in a guide is accepted by the CLI's parser."""
        rejected = [
            f"{name}: pyntpot {' '.join(args)}"
            for name, args in _guide_commands()
            if not _parses(args)
        ]
        capfd.readouterr()
        assert not rejected, f"commands the CLI rejects: {rejected}"


class TestTheExtractor:
    """The command extractor itself."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("```bash\npyntpot map a.gpx -o b.png\n```", [["map", "a.gpx", "-o", "b.png"]]),
            ("```bash\n$ uv run pyntpot map a.gpx\n```", [["map", "a.gpx"]]),
            ("```bash\npyntpot map a.gpx \\\n  --cache c\n```", [["map", "a.gpx", "--cache", "c"]]),
            ("pyntpot map outside.gpx", []),
            ("```bash\nuv run pytest\n```", []),
            ("```text\npyntpot map: error: bad\n```", []),
            ("1. Run:\n\n   ```bash\n   pyntpot map a.gpx\n   ```", [["map", "a.gpx"]]),
        ],
        ids=[
            "plain",
            "prompt-and-uv",
            "continued",
            "outside-a-fence",
            "other-command",
            "output",
            "indented",
        ],
    )
    def test_command_lines(self, text: str, expected: list[list[str]]) -> None:
        """Command lines are found in shell-tagged fenced blocks only, with prompts and continuations handled."""
        assert command_lines(text) == expected

    def test_a_misspelt_option_is_rejected(self, capfd: pytest.CaptureFixture[str]) -> None:
        """A misspelt option fails the parse, so a guide carrying one fails the check."""
        (args,) = command_lines("```bash\npyntpot map a.gpx -o b.png --cache c --contct x\n```")
        assert not _parses(args)
        capfd.readouterr()
