"""The casing union model: which basemap line classes share one ring, and what refuses a union.

Key names: `membership_problems`, the problems of the unions' membership alone (an empty union,
an unknown class, the route, a class twice, a union across water and road); `union_problems`,
the same followed by the problems the unions have against a table of stacks (a member with no
casing or reserve, casings that differ in colour or strength, mixed kinds, differing pools).

A casing union is a list of basemap line classes of one group, water or road, whose rings are
laid as one: a road over a river still reads as a crossing, and the ring of two roads that meet
is not cut by either. Its members share one ring effect, so the ring is one colour, strength and
width rule, and a union takes casings or reserves, never both. The route joins no union: it is
cased at compose from its own mask.

Every message of a union problem is written here, so a check at load and the style group's own
refusal read alike. The caller locates the problem: each is a union index, a member index or
`None`, and the message.

Does not read a theme, locate a line, paint, or build a style: it is pure, and imports only the
line effect model, which the style group and the loader both import.

Invariants: a problem's union index is a position in the unions given; a member index is a
position in that union; a union that is fine returns nothing.
"""

from collections.abc import Mapping, Sequence

from pyntpot.ink import Casing, Reserve
from pyntpot.ink.naming import did_you_mean
from pyntpot.maps.line_effects import ROAD_GROUP, WATER_GROUP, EffectStack

#: One problem: the union's index, the member's index or `None`, and the message.
type Problem = tuple[int, int | None, str]

_ROUTE_MESSAGE = "the route is cased at compose from its own mask and joins no union"
_KIND_MESSAGE = "a union is all casings or all reserves, with one pool"


def membership_problems(unions: Sequence[Sequence[str]]) -> tuple[Problem, ...]:
    """The problems of `unions`' membership, without looking at any stack.

    Args:
        unions: Each union as its member classes.

    Returns:
        One entry per problem, in union then member order: an empty union, a member that is no
        basemap class, the route, a class already in an earlier union or twice in one, and a
        union that mixes the water and the road classes.
    """
    found: list[Problem] = []
    where: dict[str, int] = {}
    known = (*WATER_GROUP, *ROAD_GROUP)
    for index, union in enumerate(unions):
        if not union:
            found.append((index, None, "names no class"))
        for at, name in enumerate(union):
            if name == "route":
                found.append((index, at, _ROUTE_MESSAGE))
            elif name not in known:
                found.append(
                    (index, at, f"{name!r} is not a basemap line class{did_you_mean(name, known)}")
                )
            elif name in where:
                found.append((index, at, f"{name} is already in casing_unions.{where[name]}"))
            else:
                where[name] = index
        found.extend(_mixed(index, union))
    return tuple(found)


def _mixed(index: int, union: Sequence[str]) -> list[Problem]:
    """The one problem of the union at `index` when it holds both water and road classes."""
    water = next((name for name in union if name in WATER_GROUP), None)
    road = next((name for name in union if name in ROAD_GROUP), None)
    if water is None or road is None:
        return []
    message = (
        f"mixes water ({water}) and road ({road}); a union lies within one group, "
        "so a road over a river still reads as a crossing"
    )
    return [(index, None, message)]


def union_problems(
    stacks: Mapping[str, EffectStack], unions: Sequence[Sequence[str]]
) -> tuple[Problem, ...]:
    """The problems of `unions`: membership first, then each against the basemap `stacks`.

    Args:
        stacks: The basemap's stack per line class; a class with none is absent.
        unions: Each union as its member classes.

    Returns:
        `membership_problems(unions)`, then one entry per problem against `stacks`: a member
        with no casing or reserve, casings that differ in colour or strength, mixed kinds and
        reserves whose pools differ. A member that is no basemap class is left to membership.
    """
    found = list(membership_problems(unions))
    for index, union in enumerate(unions):
        found.extend(_stack_problems(index, union, stacks))
    return tuple(found)


def _ring(stack: EffectStack | None) -> Casing | Reserve | None:
    """The casing or reserve `stack` holds, or `None` when it has neither."""
    if stack is None:
        return None
    return next((e for e in stack.effects if isinstance(e, Casing | Reserve)), None)


def _stack_problems(
    index: int, union: Sequence[str], stacks: Mapping[str, EffectStack]
) -> list[Problem]:
    """The problems the union at `index` has against `stacks`."""
    found: list[Problem] = []
    rings: list[tuple[str, Casing | Reserve]] = []
    for at, name in enumerate(union):
        if name == "route" or name not in (*WATER_GROUP, *ROAD_GROUP):
            continue
        ring = _ring(stacks.get(name))
        if ring is None:
            message = (
                f"{name} has no casing or reserve; give it one in line_effects, "
                "or drop it from the union"
            )
            found.append((index, at, message))
        else:
            rings.append((name, ring))
    if rings:
        found.extend((index, None, message) for message in _disagreements(rings))
    return found


def _disagreements(rings: list[tuple[str, Casing | Reserve]]) -> list[str]:
    """The message for rings that cannot share one (kinds, colour, strength or pool), if any."""
    first_name, first = rings[0]
    for name, ring in rings[1:]:
        if type(ring) is not type(first) or _shared(ring) != _shared(first):
            if isinstance(first, Casing) and isinstance(ring, Casing):
                return [_colour_message(first_name, first, name, ring)]
            return [_KIND_MESSAGE]
    return []


def _shared(ring: Casing | Reserve) -> tuple[object, ...]:
    """What the members of one union must share: a casing's colour and strength, a reserve's pool."""
    if isinstance(ring, Casing):
        return (ring.colour, ring.strength)
    return (ring.pool,)


def _colour_message(first_name: str, first: Casing, name: str, ring: Casing) -> str:
    """The refusal of the casing `ring` of `name` that differs from `first` of `first_name`."""
    return (
        f"{first_name}'s casing is {first.colour} at {first.strength:g} and "
        f"{name}'s is {ring.colour} at {ring.strength:g}; a union takes one colour and strength"
    )
