# A snapshot of the public signatures could show every surface change in review

GitHub issue: [#194](https://github.com/findlaywebb/pyntpot/issues/194)

**What exists today.** `tests/unit/test_public_api.py` pins the names each layer exports,
and `tests/architecture/test_public_signatures.py` checks that every name a public
signature reaches is public (ADR 0068). Neither shows a changed parameter, default or
return type: a signature can change and no test or diff says so.

**What the feature would add.** A pinned, generated snapshot of every public signature,
committed, so any surface change shows in review as a diff of that file and a stale
snapshot fails a test.

**Possible shape.** A small script that walks the public objects with griffe (as the
public-signature gate does) and writes one line a signature, sorted; a test that
regenerates it and compares with the committed copy, failing with the command that
refreshes it.
