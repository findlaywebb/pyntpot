"""Run a tutorial script in examples/ the way its test does: load it without its main block, call its `main`, return the file it wrote."""

import runpy
import sys
from pathlib import Path
from typing import Any

from support import REPO_ROOT

#: The tutorial scripts, one per rung.
EXAMPLES_DIR: Path = REPO_ROOT / "examples"


def load_example(stem: str, run_name: str) -> dict[str, Any]:
    """Run `examples/<stem>.py` as `run_name` and return its namespace.

    `EXAMPLES_DIR` is on `sys.path` for the call and restored after, because `runpy.run_path`
    on a single file does not put its directory there, so a script's `from labelled_grid
    import ...` would otherwise raise `ModuleNotFoundError`.

    Args:
        stem: The script's file name without `.py`.
        run_name: The `__name__` the script runs under; anything but `__main__` skips its main block.

    Returns:
        The script's global namespace once it has run.
    """
    saved = list(sys.path)
    sys.path.insert(0, str(EXAMPLES_DIR))
    try:
        return runpy.run_path(str(EXAMPLES_DIR / f"{stem}.py"), run_name=run_name)
    finally:
        sys.path[:] = saved


def run_example(stem: str, out_dir: Path, **options: object) -> Path:
    """Load `examples/<stem>.py` under a name other than `__main__`, call its `main`, return its path.

    Args:
        stem: The script's file name without `.py`.
        out_dir: The directory the script writes into.
        **options: Keyword arguments passed on to the script's `main`.

    Returns:
        The path of the finished image the script's `main` returns.
    """
    namespace = load_example(stem, f"example_{stem}")
    written = namespace["main"](out_dir, **options)
    assert isinstance(written, Path), f"examples/{stem}.py's main returned {written!r}"
    return written
