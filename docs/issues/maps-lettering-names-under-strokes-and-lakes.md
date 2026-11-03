# Names are lettered under a river's stroke, a road, or a lake blob

GitHub issue: [#52](https://github.com/findlaywebb/pyntpot/issues/52)

"Magdalen Bridge" on the Oxford card is lettered across several roads, which a city theme
with `roads = "all"` draws densely; the placer's road penalty (`on_road`, one road or none)
is the same as in a village.

Found by the round-2 map critique (2026-10-25).

Fixed so far: "Afon Arddu" under a small lake (ADR 0047), and "Cherwell" written over its
own channels, priced since ADR 0065 for the water under the letters of a name set along a
line.

To show it: paint the Oxford place card from `tests/fixtures/` and look at the name.

Not enough on its own: counting the roads under a seat (tried in ADR 0065's window: the
first in full, each further one at half, three at most) moved no name on Oxford, because
every seat within `LEADER_RUNGS` (64 px) of the bridge's pin lies across three streets or
on the Cherwell and its meadow. A fix needs seats further out, which is the leader pricing
of the placement tuning feature (#113), as well as the road count.
