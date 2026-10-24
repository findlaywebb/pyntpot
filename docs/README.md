# docs/

The canonical design docs. Read before non-trivial work.

Reading order:

1. `architecture.md`: package layout and the boundary.
2. `../GLOSSARY.md`: canonical terms; one name per concept, no synonyms.
3. `decisions/`: ADRs. Add one for any boundary or public-API change.

New design knowledge goes here (or an ADR). Schedules and roadmap live in `specs/`, never
in source docstrings (an architecture test enforces that).

Readers new to pyntpot start at `docs/index.md`, the front page of the docs. The pages written
for users are:

- `index.md`: the landing page, one painting and four routes.
- `gallery.md`: every picture in the docs, with the script that paints it.
- `tutorials/`: learn by painting, then `tutorials/painting-with-python/`.
- `how-to/`: one task per guide.
- `reference/`: the command line, style fields, cache, manifest, pigments, brushes, glossary.
- `explanation/`: how the wash works, the hand and the nib, the data policy, performance, references.

Subfolders:

- `decisions/`: Architecture Decision Records (`NNNN-title.md`).
- `explanation/`: background and the references bibliography.
- `runbooks/`: operational playbooks (dependency updates, releases).
- `issues/`: one markdown file per out-of-scope issue found while doing something else.
- `features/`: one markdown file per candidate feature: behaviour the library does not have
  and could add, recorded so it is not mistaken for a defect.
- `../specs/001-port/p7-research.md` sections 7 to 9: the maintainer's records (focus places, Welsh names, tracks).
