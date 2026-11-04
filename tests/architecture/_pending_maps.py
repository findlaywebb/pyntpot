"""The maps lane's pending violations of the public-surface gates.

It holds every path under `pyntpot.maps.` that is not under
`pyntpot.maps.lettering.pipeline.`.

This is the ratchet of plan 006: `test_public_signatures.py` and `test_field_docs.py`
fail on a violation not listed here and on a listed entry that no longer violates, so the
sets only shrink. The maps lane empties both; then the ratchet is deleted.
"""

#: Private canonical paths a public signature reaches today.
SIGNATURES: frozenset[str] = frozenset[str]()

#: Checked classes and module attributes whose fields or docstring break the field rule today.
FIELD_DOCS: frozenset[str] = frozenset[str]()
