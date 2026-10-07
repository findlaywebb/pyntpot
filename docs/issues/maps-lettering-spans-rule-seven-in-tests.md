# Tests still call the route rule "rule seven"

`pyntpot.maps.lettering.spans`, `span_clear` and `span_ends` used to name the
rule that a span's mark never comes within the clearance of the route "rule
seven", a number from a list that exists nowhere in the repository. P6
renamed it "the route rule" in those docstrings and comments, the name
`spans.py` already used elsewhere.

Three test docstrings in `tests/unit/maps/lettering/test_spans.py` still say
"rule seven". P6.5 does not edit `tests/**`.

Possible fix: reword those three docstrings to "the route rule".
