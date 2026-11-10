"""Theme files for the loader's tests: inline YAML or a file on disk, read as the loader reads."""

from pathlib import Path

from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_read import ThemeFile, read_theme
from pyntpot.maps.theme_scope import ThemeScope


def theme_file(text: str, name: str = "t.yaml") -> ThemeFile:
    """Read `text` as the theme file `name`, as the loader reads a file from disk."""
    return read_theme(Path(name), text)


def theme_file_at(path: Path) -> ThemeFile:
    """Read the theme file at `path` as UTF-8 text."""
    return read_theme(path, path.read_text(encoding="utf-8"))


def write_theme(root: Path, name: str, text: str) -> Path:
    """Write `text` to `root / name`, making its directories, and return the path."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def scope_of(text: str) -> ThemeScope:
    """The scope after checking the theme `text`, with no style groups, in the built-in scope."""
    return check_theme_scoped(theme_file(text), {}, ThemeScope.built_in())[2]
