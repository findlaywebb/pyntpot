# 0021 — Every technique cites its source

Status: accepted

## Context

The code implements techniques from papers, blogs and standards. Without a recorded
source, a later reader cannot tell a deliberate choice from an invention, and a reader
cannot check the code against what it claims to implement.

## Decision

Every technique the code implements has one entry in `docs/explanation/references.md`:
a key, a canonical source, the design inputs read when the technique was designed (the
canonical source stands in where the original reading is not recoverable) and an
`Implemented in:` line of dotted paths. The implementing module, class, function or
method names the entry in its docstring, in the line
``Source: `<key>` in docs/explanation/references.md.``

Sources are verified live and never taken from memory; each entry records how and when it
was checked.

### The references test

`tests/architecture/test_reference_keys.py` is a gate. It fails when:

- a path in an entry's `Implemented in:` line resolves to no site, or to a site whose
  docstring does not cite that entry's key;
- a docstring cites a key whose entry does not list that site;
- an entry has no `Implemented in:` site; or
- a key heading appears twice.

Nested functions are never sites. Further tests run the parser on literal text, so the
gate cannot pass by parsing nothing.

## Consequences

- Adding a technique means adding its entry and its citation line together, or the gate
  fails.
- Renaming or moving a cited site means updating `references.md`.
