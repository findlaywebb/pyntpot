"""Docstring-convention gate — designed gaps are capability facts, not schedules.

Source docstrings (module, class, function) state what a thing does and which
gaps are deliberate as CAPABILITY facts ("no consumer yet"), never as roadmap
or spec numbers. Schedules live in ``specs/`` and ``docs/``; a ``spec 002``
reference in a docstring rots the moment the roadmap shifts and couples the
implementer contract to a plan it should outlive.

Scanning
--------
Every ``*.py`` under ``src`` is parsed; all docstrings reachable
via ``ast.get_docstring`` (module + every class/function node) are checked
against the spec-number pattern. Only production source is scanned, not tests
or docs (which keep their schedule references by design).
"""

import ast
import re

from ._ast_checks import PACKAGES, REPO_ROOT, _source_files

_SPEC_NUMBER = re.compile(r"(?i)\bspec\s*[- ]?\d{3}\b")

_FAILURE = (
    "roadmap/spec numbers in source docstrings — state designed gaps as "
    "capability facts; schedules live in specs/ and docs/"
)


def _docstring_violations() -> list[str]:
    """Return ``path:lineno`` for every source docstring naming a spec number."""
    found: list[str] = []
    for path in _source_files(PACKAGES):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(
                node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
            ):
                continue
            doc = ast.get_docstring(node)
            if doc and _SPEC_NUMBER.search(doc):
                lineno = getattr(node, "lineno", "?")
                found.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
    return found


def test_source_docstrings_carry_no_spec_numbers() -> None:
    """No source docstring under src references a spec/roadmap number."""
    assert not _docstring_violations(), f"{_FAILURE}: {_docstring_violations()}"
