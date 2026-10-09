"""Run a tutorial script in examples/ the way its test does: load it without its main block, call its `main`, return the file it wrote."""

import runpy
from pathlib import Path

from support import REPO_ROOT

#: The tutorial scripts, one per rung.
EXAMPLES_DIR: Path = REPO_ROOT / "examples"


def run_example(stem: str, out_dir: Path, **options: object) -> Path:
    """Load `examples/<stem>.py` under a name other than `__main__`, call its `main`, return its path.

    Args:
        stem: The script's file name without `.py`.
        out_dir: The directory the script writes into.
        **options: Keyword arguments passed on to the script's `main`.

    Returns:
        The path of the finished image the script's `main` returns.
    """
    namespace = runpy.run_path(str(EXAMPLES_DIR / f"{stem}.py"), run_name=f"example_{stem}")
    written = namespace["main"](out_dir, **options)
    assert isinstance(written, Path), f"examples/{stem}.py's main returned {written!r}"
    return written
