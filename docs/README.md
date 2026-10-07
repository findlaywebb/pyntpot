# docs/

The canonical design docs. Read before non-trivial work.

Reading order:

1. `architecture.md`: package layout and the boundary.
2. `../GLOSSARY.md`: canonical terms; one name per concept, no synonyms.
3. `decisions/`: ADRs. Add one for any boundary or public-API change.

New design knowledge goes here (or an ADR). Schedules and roadmap live in `specs/`, never
in source docstrings (an architecture test enforces that).

Subfolders:

- `decisions/`: Architecture Decision Records (`NNNN-title.md`).
- `explanation/`: background and the references bibliography.
- `runbooks/`: operational playbooks (dependency updates, releases).
- `issues/`: one markdown file per out-of-scope issue found while doing something else.
