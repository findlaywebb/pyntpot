"""Theme files for the loader's tests: `theme_file` reads inline YAML as the loader does."""

from pathlib import Path

from pyntpot.maps.theme_read import ThemeFile, read_theme


def theme_file(text: str, name: str = "t.yaml") -> ThemeFile:
    """Read `text` as the theme file `name`, as the loader reads a file from disk."""
    return read_theme(Path(name), text)
