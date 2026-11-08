"""Theme files for the loader's tests: inline YAML or a file on disk, read as the loader reads."""

from pathlib import Path

from pyntpot.maps.theme_read import ThemeFile, read_theme


def theme_file(text: str, name: str = "t.yaml") -> ThemeFile:
    """Read `text` as the theme file `name`, as the loader reads a file from disk."""
    return read_theme(Path(name), text)


def theme_file_at(path: Path) -> ThemeFile:
    """Read the theme file at `path` as UTF-8 text."""
    return read_theme(path, path.read_text(encoding="utf-8"))
