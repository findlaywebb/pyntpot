# The bend's broken-outside refusal can never run

GitHub issue: [#141](https://github.com/findlaywebb/pyntpot/issues/141)

Area: maps (lettering).

`pyntpot.maps.lettering.span_sides.curved_side` moves a span to the outside of its bend
only when the bend's weighted strength beats the free-paper margin. It also refuses the
move when the outside's mark is broken (`_mark_broken`) and the free-paper side's is
not. Its docstring says that over the four cached tracks this refusal "turns the term
from roughly even into clearly worth having".

The refusal cannot fire with the current mark:

- `span_line` ends in `span_clear.clear_of`, which returns a mark clear of the route or
  an empty list. So a drawn mark is never "not clear", and broken only ever means empty.
- `_convex_side` names the drawn side as the outside whenever the other side's mark is
  empty. So the outside's mark is never the empty one.

In #54's sweep (spec 004), all 37 stretches with exactly one side broken had the
unbroken side as the outside, and no non-empty mark was broken.

The branch is dead code, and the docstring's claim about it does not hold for this code.

Possible fix: delete the refusal and the docstring paragraph. Or, if a broken outside
should still block the move, give `_convex_side` a way to name an empty side as the
outside and test that case.
