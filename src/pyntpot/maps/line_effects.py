"""The line effect model: a stack of casing or reserve, glow and shadow, the line classes and presets.

Key types and names: `EffectStack`, the ordered effects of one line class (at most one casing,
one glow and one shadow, or a reserve in place of the casing, all from `pyntpot.ink`); `LINE_CLASSES`, the eight classes a stack can
be set on, the basemap's seven and `route`; `WATER_GROUP` and `ROAD_GROUP`, the basemap classes in
the order the painter draws them; `BUILT_IN_PRESETS`, the three effect presets the package ships,
`cased`, `halo` and `lifted`; `checked_line_effects`, which the basemap group runs on its table;
`ring_effect`, a stack's casing or reserve, the step a casing union lays for its members.

A stack's widths are in display pixels; the compose and paint steps scale them to the array they
lay the stack on. An effect is off at a strength of 0, or, for a casing, a width of 0 (`-0.0`
included), or, for a reserve, a width of 0. A stack takes a casing or a reserve, never both,
because both lay a ring. A stack drops its off effects when it is built, so a stack written all off equals
`EffectStack()`, and a basemap table of such stacks equals `{}`: a value equal to off moves no
digest.

Does not draw, read a theme, resolve a name or check a number's range: the effect types in `ink`
refuse the values their pixels cannot take, and the theme loader checks a theme's display-pixel
bounds. It imports no style group and no loader module, which import it.

Invariants: a stack holds at most one effect of a kind and no off effect; `checked_line_effects`
returns only basemap classes and no empty stack.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pyntpot.ink import Casing, Glow, Reserve, Shadow
from pyntpot.ink.naming import did_you_mean

#: The water classes, in the order the painter draws them.
WATER_GROUP: tuple[str, ...] = ("major", "medium", "minor", "coast")

#: The road classes, in the order the painter draws them.
ROAD_GROUP: tuple[str, ...] = ("road_major", "lane", "track")

_BASEMAP = (*WATER_GROUP, *ROAD_GROUP)

#: Every class a stack can be set on: the seven basemap classes and the route.
LINE_CLASSES: frozenset[str] = frozenset(_BASEMAP) | {"route"}


type _Effect = Casing | Glow | Shadow | Reserve

#: The message for a stack that holds both ring effects.
CASING_OR_RESERVE = "a stack takes a casing or a reserve, not both"


def _is_off(effect: _Effect) -> bool:
    """Whether `effect` draws nothing: a strength of 0, or, for a casing or reserve, a width of 0."""
    if isinstance(effect, Casing | Reserve) and effect.width_px == 0:
        return True
    return not isinstance(effect, Reserve) and effect.strength == 0


@dataclass(frozen=True, kw_only=True)
class EffectStack:
    """The ordered effects of one line class: a casing or a reserve, one glow and one shadow.

    Attributes:
        effects: The effects in the order they are applied, none off; an off effect is dropped
            when the stack is built.
    """

    effects: tuple[Casing | Glow | Shadow | Reserve, ...] = ()

    def __post_init__(self) -> None:
        """Refuse two effects of a kind, drop the off ones and hold the rest as a tuple.

        Raises:
            ValueError: When two effects are of one kind, or a casing and a reserve are both
                present.
            TypeError: When an effect is no `Casing`, `Glow`, `Shadow` or `Reserve`.
        """
        kept: list[_Effect] = []
        seen: set[type] = set()
        for effect in self.effects:
            if not isinstance(effect, Casing | Glow | Shadow | Reserve):
                raise TypeError(f"{effect!r} is not a Casing, Glow, Shadow or Reserve")
            if type(effect) in seen:
                raise ValueError(f"a stack takes at most one {type(effect).__name__.lower()}")
            seen.add(type(effect))
            if {Casing, Reserve} <= seen:
                raise ValueError(CASING_OR_RESERVE)
            if not _is_off(effect):
                kept.append(effect)
        object.__setattr__(self, "effects", tuple(kept))


#: The effect presets the package ships; a theme preset may not reuse one of these names.
BUILT_IN_PRESETS: Mapping[str, EffectStack] = MappingProxyType(
    {
        "cased": EffectStack(effects=(Casing(width_px=1.2),)),
        "halo": EffectStack(effects=(Glow(spread_px=1.0, blur_px=2.5, strength=0.8),)),
        "lifted": EffectStack(effects=(Shadow(offset_px=1.2, blur_px=1.5, strength=0.35),)),
    }
)


def ring_effect(stack: EffectStack | None) -> Casing | Reserve | None:
    """The casing or reserve `stack` holds, or `None` when it holds neither or is `None`."""
    if stack is None:
        return None
    return next((e for e in stack.effects if isinstance(e, Casing | Reserve)), None)


def checked_line_effects(stacks: Mapping[str, EffectStack]) -> dict[str, EffectStack]:
    """The basemap's `stacks` less every empty one, after refusing a key that is no basemap class.

    Args:
        stacks: A stack per line class.

    Returns:
        A new table in `stacks`' order holding only the non-empty stacks.

    Raises:
        ValueError: Naming the key, the nearest basemap class and the seven, when a key is not
            one of the seven (`route` is set on `route_ink.effects`, not here).
    """
    for key in stacks:
        if key not in _BASEMAP:
            raise ValueError(_unknown_class(key, _BASEMAP))
    return {key: stack for key, stack in stacks.items() if stack.effects}


def _unknown_class(key: str, known: tuple[str, ...]) -> str:
    """The refusal of the basemap line-effect key `key` among the classes `known`."""
    return (
        f"line_effects key {key!r} is not a basemap line class{did_you_mean(key, known)}; "
        f"the classes are {', '.join(known)}"
    )
