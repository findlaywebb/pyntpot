"""What is wrong with a theme file: one located problem, and the error that holds them all.

Key types: `ThemeProblem`, one thing wrong with a theme file, located by file, dotted key
path and line; `ThemeError`, the `ValueError` a theme that cannot be loaded raises, holding
every problem found rather than the first.

Does not find problems: the reader, the checker and the resolver do, and hand their
problems here. Does not read files or log.

Invariants: a `ThemeError` holds at least one problem; its problems are sorted by file,
then line (a problem with no line first), then key; its message is one problem per line,
in that order.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import override


@dataclass(frozen=True, kw_only=True)
class ThemeProblem:
    """One thing wrong with a theme file.

    Attributes:
        path: The theme file, as the caller named it (a packaged theme's path inside the package).
        key: The dotted key path, such as `wash.blooms`; empty for the file as a whole.
        line: The 1-based line of the key, or `None` when the problem has no place in the file.
        message: What is wrong, and what to write instead when that is known.
    """

    path: Path
    key: str
    line: int | None
    message: str

    @override
    def __str__(self) -> str:
        """Read as `path:line: key: message`, leaving out the line and the key when absent."""
        where = str(self.path) if self.line is None else f"{self.path}:{self.line}"
        what = self.message if not self.key else f"{self.key}: {self.message}"
        return f"{where}: {what}"


class ThemeError(ValueError):
    """A theme that cannot be loaded: every problem found, in file then line order.

    Attributes:
        problems: Every problem found, sorted by file, then line, then key; never empty.
    """

    problems: tuple[ThemeProblem, ...]

    def __init__(self, problems: Sequence[ThemeProblem]) -> None:
        """Hold `problems`, sorted, with a message of one problem per line.

        Args:
            problems: Every problem found; at least one.

        Raises:
            ValueError: When `problems` is empty, a programming error.
        """
        if not problems:
            raise ValueError("a theme error needs a problem")
        self.problems = tuple(sorted(problems, key=_order))
        super().__init__("\n".join(str(problem) for problem in self.problems))


def _order(problem: ThemeProblem) -> tuple[str, int, str]:
    """The sort key of `problem`: its file, its line (0 when it has none), its key."""
    return (str(problem.path), problem.line or 0, problem.key)
