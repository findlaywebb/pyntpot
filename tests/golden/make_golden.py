"""Paint the Lynmouth fixture into a directory and compare it with others.

Run as `PYTHONPATH=tests uv run python tests/golden/make_golden.py OUT [--compare DIR ...]`.
It paints into a temporary copy of the fixture and writes the five outputs and
`plates.json` into `OUT`; when `OUT` is not the committed golden directory it
also writes `baseline.json`, the commit painted and whether the tree was dirty.
Each `--compare DIR` logs one line per output (byte-identical or not, and the
fraction of pixels past the parity channel bound) and one line with both
manifest hashes. The gate options apply to the first `--compare` only; any
violation makes the script exit 1 after every line is logged.
"""

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from golden.test_parity import MAX_CHANNEL_DELTA

from support import REPO_ROOT
from support.golden import OUTPUTS, differing_fraction, paint_fixture
from support.paths import GOLDEN_DIR

logger = logging.getLogger("make_golden")

MANIFEST = "plates.json"
LABELS = "labels.txt"


@dataclass(frozen=True)
class Gate:
    """The pass conditions checked against the first compared directory."""

    identical: frozenset[str]
    max_fraction: float | None
    hash_rule: str | None
    labels_equal: bool


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Paint the Lynmouth fixture and compare it.")
    parser.add_argument("out", type=Path, metavar="OUT", help="directory to write into")
    parser.add_argument(
        "--compare", type=Path, action="append", default=[], metavar="DIR", help="compare with DIR"
    )
    parser.add_argument(
        "--require-identical",
        nargs="+",
        default=[],
        metavar="NAME",
        choices=[*OUTPUTS, "all"],
        help="outputs that must be byte-identical; 'all' means every output",
    )
    parser.add_argument(
        "--max-fraction", type=float, default=None, help="bound on every other output"
    )
    parser.add_argument(
        "--require-hash", choices=["equal", "differ"], default=None, help="manifest hash rule"
    )
    parser.add_argument(
        "--require-labels-equal", action="store_true", help=f"{LABELS} must be equal"
    )
    return parser.parse_args(argv)


def _git(*args: str) -> str:
    """Run one git command in the repository and return its stripped output."""
    done = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def _write(out: Path) -> None:
    """Paint into a temporary copy and write the outputs, and the baseline record, to `out`."""
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        painted = paint_fixture(Path(tmp))
        for name in (*OUTPUTS, MANIFEST):
            shutil.copyfile(painted[name], out / name)
    if out.resolve() != GOLDEN_DIR:
        baseline = {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--porcelain")),
        }
        (out / "baseline.json").write_text(json.dumps(baseline) + "\n")
        logger.info("baseline: %s", baseline)


def _hash(directory: Path) -> str:
    """Return the manifest hash written in a directory."""
    return str(json.loads((directory / MANIFEST).read_text())["hash"])


def _compare(out: Path, other: Path, gate: Gate | None) -> list[str]:
    """Log one line per output and the hashes; return the gate's violations."""
    violations: list[str] = []
    for name in OUTPUTS:
        identical = (out / name).read_bytes() == (other / name).read_bytes()
        fraction = differing_fraction(out / name, other / name, MAX_CHANNEL_DELTA)
        verdict = "yes" if identical else "no"
        logger.info(
            "%s against %s: identical %s, differing fraction %.6f", name, other, verdict, fraction
        )
        if gate is None:
            continue
        if name in gate.identical and not identical:
            violations.append(f"{name} is not byte-identical")
        bound = gate.max_fraction
        if name not in gate.identical and bound is not None and fraction > bound:
            violations.append(f"{name} differing fraction {fraction:.6f} over {bound}")
    ours, theirs = _hash(out), _hash(other)
    logger.info("manifest hash: %s here, %s in %s", ours, theirs, other)
    if gate is None:
        return violations
    if gate.hash_rule is not None and (ours == theirs) != (gate.hash_rule == "equal"):
        violations.append(f"manifest hash rule '{gate.hash_rule}' violated")
    if gate.labels_equal and not _labels_equal(out, other):
        violations.append(f"{LABELS} differs")
    return violations


def _labels_equal(out: Path, other: Path) -> bool:
    """Return whether both directories hold the same placed label names."""
    ours, theirs = out / LABELS, other / LABELS
    return ours.is_file() and theirs.is_file() and ours.read_bytes() == theirs.read_bytes()


def main(argv: list[str] | None = None) -> int:
    """Paint, write and compare; return 1 when a gate option is violated, else 0."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    identical = set(OUTPUTS) if "all" in args.require_identical else set(args.require_identical)
    gate = Gate(
        identical=frozenset(identical),
        max_fraction=args.max_fraction,
        hash_rule=args.require_hash,
        labels_equal=args.require_labels_equal,
    )
    _write(args.out)
    violations: list[str] = []
    for index, other in enumerate(args.compare):
        violations += _compare(args.out, other, gate if index == 0 else None)
    for violation in violations:
        logger.error("gate violated: %s", violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
