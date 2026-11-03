r"""Every command the docs show runs as written: `pyntpot` commands parse, example commands name real options.

Reads every site page and `README.md`. Commands come from two places: each line of a
fenced `bash`, `console`, `shell`, `sh` or `text` block, after `\` continuations are
joined and a leading `$ ` and `uv run ` dropped; and each backticked span in the prose
that starts `uv run python examples/`, with `uv run ` dropped. Only lines starting
`pyntpot ` or `python examples/` are commands, so output lines in a `text` block yield
nothing. A `pyntpot` command is parsed by `pyntpot.maps.cli.build_parser`, built and never
run; an example command's script must exist, and each of its `-` tokens must be an option
string of one of the script's `add_argument` calls, read from its AST (the script is never
run). Neither check proves the files a command names exist or that it succeeds.
"""

import ast
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

import pytest

from pyntpot.maps.cli import build_parser

from support import REPO_ROOT
from support.site_pages import DOCS, fenced_blocks, site_pages

_SHELL_BLOCKS = frozenset({"bash", "console", "shell", "sh", "text"})
_COMMAND_STARTS = ("pyntpot ", "python examples/")
_INLINE = re.compile(r"`uv run (?P<command>python examples/[^`]+)`")
_USAGE = re.compile(r"^pyntpot (map )?\[")
_SCRIPT = re.compile(r"^python (?P<path>examples/\S+\.py)$")


@dataclass(frozen=True)
class Command:
    """One command a page shows: the 1-based line it starts on, and its text without prompt or `uv run`."""

    line: int
    text: str


def _strip(line: str) -> str:
    """Return a command line without its leading whitespace, `$ ` prompt and `uv run `."""
    line = line.strip().removeprefix("$ ")
    return line.removeprefix("uv run ")


def _block_commands(code: str, first_line: int) -> list[Command]:
    """Return the commands in one fenced block's code, whose first line is page line `first_line`."""
    found: list[Command] = []
    pending: list[str] = []
    start = first_line
    for offset, line in enumerate(code.splitlines()):
        if not pending:
            start = first_line + offset
        if line.rstrip().endswith("\\"):
            pending.append(line.rstrip()[:-1].strip())
            continue
        text = _strip(" ".join([*pending, line.strip()]))
        pending = []
        if text.startswith(_COMMAND_STARTS):
            found.append(Command(start, text))
    return found


def _fence_lines(text: str) -> set[int]:
    """Return the 1-based lines of `text` that a fenced block, fences included, takes."""
    taken: set[int] = set()
    for block in fenced_blocks(text):
        length = len(block.code.splitlines()) if block.code else 0
        taken.update(range(block.line, block.line + length + 2))
    return taken


def commands(text: str) -> list[Command]:
    """Return the commands a page's text shows, fenced first in page order, then inline spans in page order."""
    found: list[Command] = []
    for block in fenced_blocks(text):
        if block.lang in _SHELL_BLOCKS:
            found.extend(_block_commands(block.code, block.line + 1))
    taken = _fence_lines(text)
    for number, line in enumerate(text.splitlines(), start=1):
        if number not in taken:
            found.extend(Command(number, span["command"]) for span in _INLINE.finditer(line))
    return found


def _pages() -> list[Path]:
    """Return the site pages and the README."""
    return [*site_pages(), REPO_ROOT / "README.md"]


def _all_commands() -> list[tuple[Path, Command]]:
    """Return every (page, command) pair across the site and the README."""
    return [(page, command) for page in _pages() for command in commands(page.read_text())]


def _where(page: Path, command: Command) -> str:
    """Return a failure's location: the page relative to the repository, and the line."""
    return f"{page.relative_to(REPO_ROOT)}:{command.line}"


def _parse_error(arguments: list[str]) -> str | None:
    """Return `None` when the CLI's parser accepts `arguments`, else the exit it raised."""
    try:
        build_parser().parse_args(arguments)
    except SystemExit as exc:
        return f"argparse exited with {exc.code}"
    return None


def _script_options(script: Path) -> set[str]:
    """Return every option string a script passes to an `add_argument` call, read from its AST."""
    options: set[str] = set()
    for node in ast.walk(ast.parse(script.read_text())):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "add_argument":
            continue
        options.update(
            argument.value
            for argument in node.args
            if isinstance(argument, ast.Constant)
            and isinstance(argument.value, str)
            and argument.value.startswith("-")
        )
    return options


def _example_problem(text: str) -> str | None:
    """Return why an example command is wrong (missing script, unknown option), or `None`."""
    words = shlex.split(text, comments=True)
    found = _SCRIPT.match(" ".join(words[:2]))
    if found is None:
        return f"not a `python examples/<script>.py` command: {text!r}"
    script = REPO_ROOT / found["path"]
    if not script.is_file():
        return f"no such script {found['path']}"
    known = _script_options(script)
    unknown = [
        word
        for word in words[2:]
        if word.startswith("-") and word.split("=", maxsplit=1)[0] not in known
    ]
    return f"options {unknown} not in {found['path']}" if unknown else None


class TestTheExtractor:
    """The command extractor itself, on inline text."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                "```bash\npyntpot map a.gpx \\\n  --cache c\n```",
                [Command(2, "pyntpot map a.gpx --cache c")],
            ),
            (
                "1. Run:\n\n   ```console\n   $ uv run pyntpot map a.gpx\n   ```",
                [Command(4, "pyntpot map a.gpx")],
            ),
            (
                "Run `uv run python examples/fern.py out/` now.",
                [Command(1, "python examples/fern.py out/")],
            ),
            ("```text\nwrote out/fern.png\n```", []),
            ("```python\npyntpot map a.gpx\n```", []),
        ],
        ids=["continued", "indented-fence", "inline-example", "text-output", "python-block"],
    )
    def test_commands(self, text: str, expected: list[Command]) -> None:
        """Commands are read from shell and text fences and inline example spans, with their page lines."""
        assert commands(text) == expected

    def test_a_misspelt_option_is_rejected(self, capfd: pytest.CaptureFixture[str]) -> None:
        """A misspelt option fails the parse, so a page carrying one fails the check."""
        (command,) = commands(
            "```bash\npyntpot map a.gpx -o b.png --cache c --contact x --margn-m 5\n```"
        )
        assert _parse_error(shlex.split(command.text)[1:]) is not None
        capfd.readouterr()

    def test_an_unknown_example_option_is_named(self) -> None:
        """An option a script does not define is reported, so a page carrying one fails the check."""
        assert _example_problem("python examples/trees.py out/ --figur tree") is not None
        assert _example_problem("python examples/trees.py out/ --figure tree") is None


class TestThePagesCommands:
    """The real pages' commands against the real CLI and example scripts."""

    def test_the_command_line_guide_shows_a_pyntpot_command(self) -> None:
        """The command-line guide yields at least one command, so the parse check cannot pass on none."""
        page = DOCS / "how-to" / "map-from-the-command-line.md"
        assert any(command.text.startswith("pyntpot ") for command in commands(page.read_text()))

    def test_the_inline_example_spans_are_read(self) -> None:
        """The two prose-only example commands are among those read, so inline spans are checked."""
        texts = {command.text for _, command in _all_commands()}
        assert "python examples/curves.py out/ --figure rose" in texts
        assert "python examples/kaleidoscope.py out/" in texts

    def test_every_pyntpot_command_parses(self, capfd: pytest.CaptureFixture[str]) -> None:
        """Each `pyntpot` command a page shows, synopsis usage lines aside, is accepted by the CLI's parser."""
        rejected = [
            f"{_where(page, command)}: {command.text} ({error})"
            for page, command in _all_commands()
            if command.text.startswith("pyntpot ") and not _USAGE.match(command.text)
            for error in [_parse_error(shlex.split(command.text, comments=True)[1:])]
            if error is not None
        ]
        capfd.readouterr()
        assert not rejected, f"commands the CLI rejects: {rejected}"

    def test_every_example_command_names_a_script_and_its_options(self) -> None:
        """Each `python examples/` command names a script that exists, with only options that script defines."""
        wrong = [
            f"{_where(page, command)}: {problem}"
            for page, command in _all_commands()
            if command.text.startswith("python examples/")
            for problem in [_example_problem(command.text)]
            if problem is not None
        ]
        assert not wrong, f"example commands that do not match their scripts: {wrong}"
