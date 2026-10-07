"""Turn a pull request's diff into mutmut patterns for the functions it changed.

Run from the repository root as
`uv run python tests/mutation/scope.py --base REF --out PATH`. It diffs `REF...HEAD`
under `src/pyntpot`, keeps the `.py` files that `[tool.mutmut] only_mutate` in
`pyproject.toml` selects (mutmut's own `fnmatch` rule, where `*` spans `/`), and writes
one mutmut pattern a line to `PATH`. The PR job passes them to `mutmut run`.

Key types: a pattern is a string. `pyntpot.<module>.x_<name>*` selects a top-level
function's mutants and `pyntpot.<module>.xǁ<Class>ǁ<name>*` a method's, the names mutmut
3.8 gives them. The module part drops `src/` and `.py`, maps `/` to `.`, and drops a
trailing `.__init__`.

Invariants: a function or method counts as changed when its lines, decorators included,
meet a changed line of the new file. A pure deletion counts the new lines either side of
it. A change inside a nested function counts for its top-level enclosing function.
Output is sorted and de-duplicated.

It does not cover:

- a change outside any function or method (module constants, class attributes, imports):
  it emits nothing for it, and the nightly run covers it;
- a function or method with any decorator other than a single `staticmethod` or
  `classmethod`: mutmut generates no mutants for it, so no pattern is emitted;
- a deleted file: it has no new source and no mutants.

It repeats `shard.py`'s path-to-module and decorator rules rather than importing them, so
each script runs standalone from CI; both test files pin the same cases.
"""

import argparse
import ast
import fnmatch
import logging
import re
import subprocess
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

logger = logging.getLogger("mutation.scope")

#: mutmut's separator between `x`, the class name and the method name.
CLASS_SEPARATOR = "ǁ"
#: The only decorators mutmut 3.8 still mutates under, and only one of them alone.
PLAIN_DECORATORS = frozenset({"staticmethod", "classmethod"})

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")

type LineRange = tuple[int, int]
type Definition = ast.FunctionDef | ast.AsyncFunctionDef


def changed_ranges(diff: str) -> dict[str, list[LineRange]]:
    """Map each new-side path of a `git diff --unified=0` to its changed line ranges.

    `+c,d` with `d > 0` changes lines `c` to `c + d - 1`, `+c` alone means `d = 1`, and a
    pure deletion `+c,0` gives lines `c` and `c + 1`. A file whose new side is `/dev/null`
    is left out. File headers are read only between `diff --git` and the first hunk, so
    a changed line that looks like a header is never taken for one.
    """
    ranges: dict[str, list[LineRange]] = {}
    current: list[LineRange] | None = None
    in_header = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current, in_header = None, True
        elif in_header and line.startswith("+++ "):
            path = line.removeprefix("+++ ")
            current = (
                None if path == "/dev/null" else ranges.setdefault(path.removeprefix("b/"), [])
            )
        elif hunk := _HUNK.match(line):
            in_header = False
            if current is not None:
                current.append(_hunk_range(int(hunk["start"]), hunk["count"]))
    return ranges


def _hunk_range(start: int, count: str | None) -> LineRange:
    """Return the new-file lines one hunk touches."""
    lines = 1 if count is None else int(count)
    return (start, start + lines - 1) if lines else (start, start + 1)


def module_name(path: str) -> str:
    """Return mutmut's module name for a repository path.

    `src/pyntpot/ink/polyline.py` gives `pyntpot.ink.polyline`, and
    `src/pyntpot/ink/__init__.py` gives `pyntpot.ink`.
    """
    dotted = path.removesuffix(".py").replace("/", ".").removeprefix("src.")
    return dotted.removesuffix(".__init__")


def is_mutated(node: Definition) -> bool:
    """Return whether mutmut 3.8 generates mutants for a function or method.

    It does for an undecorated one and for one carrying a single `staticmethod` or
    `classmethod`; any other decorator, or more than one, means no mutants.
    """
    decorators = node.decorator_list
    if not decorators:
        return True
    only = decorators[0]
    return len(decorators) == 1 and isinstance(only, ast.Name) and only.id in PLAIN_DECORATORS


def definitions(tree: ast.Module) -> Iterator[tuple[str, Definition]]:
    """Yield `(mangled name, node)` for each top-level function and top-level class's method.

    The mangled name is `x_<name>` for a function and `xǁ<Class>ǁ<name>` for a method.
    """
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield f"x_{node.name}", node
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef):
                    yield f"x{CLASS_SEPARATOR}{node.name}{CLASS_SEPARATOR}{member.name}", member


def _touches(node: Definition, ranges: Sequence[LineRange]) -> bool:
    """Return whether any range meets the node's lines, decorators included."""
    first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    last = node.end_lineno or node.lineno
    return any(start <= last and first <= stop for start, stop in ranges)


def in_scope(path: str, only_mutate: Sequence[str]) -> bool:
    """Return whether mutmut mutates a path: a `.py` file matching some `only_mutate` glob."""
    return path.endswith(".py") and any(fnmatch.fnmatch(path, glob) for glob in only_mutate)


def changed_functions(
    diff: str, sources: Mapping[str, str], only_mutate: Sequence[str]
) -> list[str]:
    """Return the sorted, de-duplicated mutmut patterns for the functions a diff changes.

    Args:
        diff: A `git diff --unified=0` text.
        sources: The new source of each changed file in scope, keyed by repository path.
        only_mutate: The `[tool.mutmut] only_mutate` globs.

    Returns:
        One pattern per changed function or method that mutmut mutates.
    """
    patterns: set[str] = set()
    for path, ranges in changed_ranges(diff).items():
        if not in_scope(path, only_mutate):
            continue
        module = module_name(path)
        for mangled, node in definitions(ast.parse(sources[path], filename=path)):
            if is_mutated(node) and _touches(node, ranges):
                patterns.add(f"{module}.{mangled}*")
    return sorted(patterns)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Write mutmut patterns for changed functions.")
    parser.add_argument("--base", required=True, metavar="REF", help="diff REF...HEAD")
    parser.add_argument("--out", required=True, type=Path, metavar="PATH", help="pattern file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Diff against the base, write the changed functions' patterns, and return 0."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    command = ["git", "diff", "--unified=0", "--diff-filter=d", f"{args.base}...HEAD"]
    diff = subprocess.run(
        [*command, "--", "src/pyntpot"], check=True, capture_output=True, text=True
    ).stdout
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    only_mutate = pyproject["tool"]["mutmut"]["only_mutate"]
    sources = {
        path: Path(path).read_text(encoding="utf-8")
        for path in changed_ranges(diff)
        if in_scope(path, only_mutate)
    }
    patterns = changed_functions(diff, sources, only_mutate)
    args.out.write_text("".join(f"{pattern}\n" for pattern in patterns), encoding="utf-8")
    logger.info("%d changed functions in the mutation scope", len(patterns))
    for pattern in patterns:
        logger.info("  %s", pattern)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
