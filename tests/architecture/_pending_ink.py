"""The ink lane's pending violations of the public-surface gates.

It holds the paths under `pyntpot.ink.`.

This is the ratchet of plan 006: `test_public_signatures.py` and `test_field_docs.py`
fail on a violation not listed here and on a listed entry that no longer violates, so the
sets only shrink. The ink lane empties both; then the ratchet is deleted.
"""

#: Private canonical paths a public signature reaches today.
SIGNATURES: frozenset[str] = frozenset[str]()

#: Checked classes and module attributes whose fields or docstring break the field rule today.
FIELD_DOCS: frozenset[str] = frozenset[str]()
