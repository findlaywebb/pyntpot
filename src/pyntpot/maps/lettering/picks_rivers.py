"""Which watercourses a card names, by run inside the card and nearness to the route.

Key names: `pick_rivers`, the labels for the best rivers, each carrying its water as its
baseline; `river_name`, a river's name without its "River".

It does not pick settlements or roads, and it does not place a name.

Invariants: the major river alone may be lettered twice, and only when it crosses most of
the map.
"""

import math
import re

from pyntpot.ink.chains import joined
from pyntpot.ink.polyline import Pt, cumulative_length, length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_RIVER, Label, feature_px
from pyntpot.maps.lettering.picks_lines import NamedLines
from pyntpot.maps.lettering.placement_names import MAJOR_RIVER_LABELS
from pyntpot.maps.lettering.placement_window import _on_line

#: How much water a name needs under it before it is written on the water, as a
#: multiple of its own type size. Two and a bit: the letters occupy about one
#: type size of band, so this leaves better than half a size of water either
#: side of them. Measured against the width the river is *typically* drawn at
#: rather than its widest point, because a name set on the water may be set
#: anywhere along it.
IN_WATER_CAPS = 2.2


#: How many watercourses a map names. The major one always, and the best
#: medium only when it is worth having beside it. Never a brook.
RIVER_MAX = 2
#: The fewest points a watercourse needs to be a line.
MIN_LINE_POINTS = 2
RIVER_REL_FLOOR = 0.2

#: How much water a river has to have on the map before it is lettered twice,
#: as a share of the card's longer side. The reason for the second name is that
#: a river crossing the whole map is read in pieces; a river clipping a corner
#: is read in one, and the second name has nowhere to go but away from its own
#: water. With a single major watercourse on the map and only 295 px of
#: water on a 900 px map, it would take both allowances and write the second
#: one in open paper past the end of the river. The allowance is earned by the
#: run, not by the rank.
MAJOR_RIVER_TWICE_FRAC = 0.55


def pick_rivers(
    basemap: Basemap,
    lines: NamedLines,
    card: Card,
    route_px: list[Pt],
    budget: int = RIVER_MAX,
) -> list[Label]:
    """Which watercourses the map names, by run inside the card and proximity.

    The painting classes answer "how wide is the brush" and are computed from
    run length alone, which cannot separate two tributaries of the same length.
    What separates them on a ride is the route: the one it crossed is the one
    worth naming.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in display pixels.
        budget: How many to letter.

    Returns:
        One `Label` a river, best first, anchored on its own water and carrying
        the water as its baseline.
    """
    geom = lines.get("rivers") or []
    thin = route_px[::3] or route_px
    typical: dict[str, float] = {}
    scored: list[tuple[float, str, list[Pt]]] = []
    widths: dict[str, float] = {}
    for entry in geom:
        name = str(entry.get("n") or "")
        if not name or entry.get("c") == "minor":
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) < MIN_LINE_POINTS:
            continue
        run_m = length(line) / max(card.scale, 1e-9)
        near_m = min(min(math.dist(p, q) for q in thin) for p in line[::2]) / max(card.scale, 1e-9)
        score = run_m / 1000.0 * min(max(1.0 - near_m / 500.0, 0.2), 1.0)
        widths[name] = max(
            widths.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("w") or 0.0)),
        )
        # The width the river is typically drawn at, which is what decides
        # whether its own name fits in it.
        typical[name] = max(
            typical.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("wn") or 0.0)),
        )
        scored.append((score, name, line))
    # One river arrives as a dozen ways. A name may go anywhere along its own
    # watercourse, and that freedom is only real if the watercourse is one
    # line, so the pieces are chained end to end first, exactly as a road's
    # are, and the longest chain is the river's baseline.
    pieces: dict[str, list[list[Pt]]] = {}
    totals: dict[str, float] = {}
    for score, name, line in scored:
        pieces.setdefault(name, []).append(line)
        totals[name] = totals.get(name, 0.0) + score
    merged: dict[str, tuple[float, list[Pt]]] = {
        name: (totals[name], max(joined(parts), key=length)) for name, parts in pieces.items()
    }
    order = sorted(merged.items(), key=lambda kv: -kv[1][0])
    out: list[Label] = []
    for rank, (name, (score, line)) in enumerate(order[:budget]):
        if out and score < RIVER_REL_FLOOR * order[0][1][0]:
            break
        # The major river is the first, and it is the only one lettered twice.
        # The two are anchored at the third and at the two-thirds point of the
        # water so the placer starts them in different halves; each is then free
        # to move anywhere along the whole line from there, and the repeat guard
        # in `place` keeps them from converging on the same window.
        run = length(line)
        twice = run >= MAJOR_RIVER_TWICE_FRAC * max(card.w, card.h)
        times = MAJOR_RIVER_LABELS if rank == 0 and twice else 1
        for n in range(times):
            at = (n + 1) / (times + 1)
            anchor = _on_line(line, cumulative_length(line), run * at)[0]
            size = DEFAULT_LINE_PX * 0.9
            out.append(
                Label(
                    name=river_name(name),
                    kind="river",
                    why=name,
                    px=anchor[0],
                    py=anchor[1],
                    tier=TIER_RIVER,
                    size=size,
                    baseline=line,
                    in_water=typical.get(name, 0.0) >= size * IN_WATER_CAPS,
                    feature_px=widths.get(name, 0.0),
                )
            )
    return out


def river_name(name: str) -> str:
    """A river's name without its "River", since the water it is written on says the rest."""
    return re.sub(r"^River\s+", "", str(name)).strip() or str(name)
