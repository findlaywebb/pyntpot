"""The theme schema's regenerator: the model in, both committed schema files out.

Writes `theme_schema()` as indented JSON to `src/pyntpot/maps/themes/theme.schema.json`,
which the package ships, and `docs/reference/theme.schema.json`, which the docs site
serves at the schema's `$id`. Run as `PYTHONPATH=tests uv run python -m support.theme_schema`.

It does not check theme files or compare the committed copies; the schema tests do.
"""

import json
import logging
from pathlib import Path

from pyntpot.maps.theme_schema import theme_schema

from support import REPO_ROOT

_log = logging.getLogger(__name__)

#: The command that regenerates both files from the model.
REGENERATE = "PYTHONPATH=tests uv run python -m support.theme_schema"

#: The two committed copies of the schema: the package's and the docs site's.
SCHEMA_FILES: tuple[Path, ...] = (
    REPO_ROOT / "src" / "pyntpot" / "maps" / "themes" / "theme.schema.json",
    REPO_ROOT / "docs" / "reference" / "theme.schema.json",
)


def main() -> None:
    """Write the schema the model generates to both committed paths."""
    text = json.dumps(theme_schema(), indent=2, sort_keys=False) + "\n"
    for path in SCHEMA_FILES:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        _log.info("wrote %s", path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
