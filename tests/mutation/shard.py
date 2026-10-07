"""Split the mutation scope into shards, largest module first.

Run from the repository root. `uv run python tests/mutation/shard.py --index I --out PATH`
writes shard `I`'s mutmut patterns, one a line, to `PATH`;
`--matrix-out PATH` instead appends `indices=[0, ..., N-1]` (JSON) to `PATH`, which the
mutation workflow's `plan` job, in its all mode, passes as `$GITHUB_OUTPUT`. `--count N` defaults to
`[tool.pyntpot.mutation] shards` in `pyproject.toml`.

Key types: a module is mutmut's dotted module name (`pyntpot.ink.polyline`; a package's
`__init__.py` gives `pyntpot.ink`), and its cost is its source line count, the proxy for
its mutation time. A shard is the sorted list of patterns `<module>.x_*` and
`<module>.xǁ*` for each of its modules. Two patterns rather than `<module>.*`, because a
package's module name prefixes its submodules' names.

Invariants: modules go largest first (ties by name) onto the shard with the lowest
running cost (ties to the lowest index), so the same scope and count always give the
same shards. Only `.py` files that `[tool.mutmut] only_mutate` selects, with at least
one function or method mutmut mutates, are modules. No shard is empty: an empty one
would run `mutmut run` with no pattern, which tests every mutant.

It does not balance by measured time, and it repeats `scope.py`'s path-to-module and
decorator rules rather than importing them, so each script runs standalone from CI;
both test files pin the same cases.
"""

import argparse
import ast
import fnmatch
import json
import logging
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

logger = logging.getLogger("mutation.shard")

#: mutmut's separator between `x`, the class name and the method name.
CLASS_SEPARATOR = "ǁ"
#: The only decorators mutmut 3.8 still mutates under, and only one of them alone.
PLAIN_DECORATORS = frozenset({"staticmethod", "classmethod"})

type Definition = ast.FunctionDef | ast.AsyncFunctionDef


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


def _has_mutated_definition(tree: ast.Module) -> bool:
    """Return whether a module has a top-level function or class method mutmut mutates."""
    for node in tree.body:
        members = node.body if isinstance(node, ast.ClassDef) else [node]
        for member in members:
            if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef) and is_mutated(member):
                return True
    return False


def module_costs(sources: Mapping[str, str], only_mutate: Sequence[str]) -> dict[str, int]:
    """Map each in-scope module with a mutated function to its source line count.

    Args:
        sources: Source text keyed by repository path (`src/pyntpot/...`).
        only_mutate: The `[tool.mutmut] only_mutate` globs.

    Returns:
        Module name to line count, for the `.py` paths a glob matches.
    """
    return {
        module_name(path): len(text.splitlines())
        for path, text in sources.items()
        if path.endswith(".py")
        and any(fnmatch.fnmatch(path, glob) for glob in only_mutate)
        and _has_mutated_definition(ast.parse(text, filename=path))
    }


def shard_patterns(modules: Mapping[str, int], count: int) -> list[list[str]]:
    """Assign modules to `count` shards, largest first, and return each shard's patterns.

    Args:
        modules: Module name to cost (source line count).
        count: The number of shards.

    Returns:
        Per shard, the sorted patterns `<module>.x_*` and `<module>.xǁ*` of its modules.

    Raises:
        ValueError: `count` is below 1 or above the number of modules.
    """
    if not 1 <= count <= len(modules):
        raise ValueError(f"shard count {count} is not between 1 and {len(modules)} modules")
    costs = [0] * count
    shards: list[list[str]] = [[] for _ in range(count)]
    for module, cost in sorted(modules.items(), key=lambda item: (-item[1], item[0])):
        index = min(range(count), key=costs.__getitem__)
        costs[index] += cost
        shards[index] += [f"{module}.x_*", f"{module}.x{CLASS_SEPARATOR}*"]
    return [sorted(patterns) for patterns in shards]


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Write one mutation shard's mutmut patterns.")
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument("--index", type=int, metavar="I", help="the shard to write")
    task.add_argument("--matrix-out", type=Path, metavar="PATH", help="append the indices")
    parser.add_argument("--count", type=int, metavar="N", help="shards (default: pyproject)")
    parser.add_argument("--out", type=Path, metavar="PATH", help="pattern file for --index")
    args = parser.parse_args(argv)
    if args.index is not None and args.out is None:
        parser.error("--index needs --out")
    return args


def main(argv: list[str] | None = None) -> int:
    """Write one shard's patterns, or the matrix indices, and return 0."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    count = (
        args.count if args.count is not None else pyproject["tool"]["pyntpot"]["mutation"]["shards"]
    )
    if args.matrix_out is not None:
        indices = json.dumps(list(range(count)))
        with args.matrix_out.open("a", encoding="utf-8") as out:
            out.write(f"indices={indices}\n")
        logger.info("indices=%s", indices)
        return 0
    sources = {str(path): path.read_text(encoding="utf-8") for path in Path("src").rglob("*.py")}
    modules = module_costs(sources, pyproject["tool"]["mutmut"]["only_mutate"])
    patterns = shard_patterns(modules, count)[args.index]
    args.out.write_text("".join(f"{pattern}\n" for pattern in patterns), encoding="utf-8")
    logger.info("shard %d of %d: %d modules", args.index, count, len(patterns) // 2)
    for pattern in patterns:
        logger.info("  %s", pattern)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
