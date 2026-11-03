# The route's start place could always be lettered

GitHub issue: [#132](https://github.com/findlaywebb/pyntpot/issues/132)

**What exists today.** `pick_settlements` (`maps/lettering/picks_settlements.py`) chooses which
settlements the place card letters, by its own rules. Nothing in them treats the place the
route starts in as special, so a start place is lettered only when those rules happen to pick
it, and a card can leave its own start unnamed.

**Where it came from.** The note for #47 (landmark names forty characters long) found, on the
Lynmouth command-line card, that the town's own name was not lettered. Its possible fix had
three parts: drop landmark names over about 25 characters, rank places of worship below
landmarks, and always letter the place the route starts in. ADR 0063 (the #47 fix) did the
first part as a demotion, left places of worship alone, and did not do the third: always
lettering the start place is a settlement-picking rule, not a landmark one, so it was left to
its own change. On the Lynmouth card "Lynton" is lettered by the settlement rules, so the card
no longer shows the gap, but the rule is still not guaranteed.

**What the feature would add.** The settlement pick always includes the settlement the route
starts in, whatever the other rules would have chosen, and the placer seats it before the
other settlements.

**Open questions.**
- How "the place the route starts in" is found: the nearest settlement to the first route
  point, the settlement whose area holds it, or the start place a caller names.
- What a route that starts in open country does: no start place, or the nearest one within a
  stated distance.
- Whether the start place counts against the settlement cap, and what it displaces when it
  is full.

**Possible shape.** `pick_settlements` takes the route's first point, finds the start
settlement, and adds it to the picks ahead of the cap. It changes which names a card letters,
so it moves the lettered goldens of every card whose start was not already picked, and needs
a regeneration window of its own with an ADR (as ADR 0063 did).
