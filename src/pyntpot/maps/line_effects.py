"""The line effect model: a stack of casing, glow and shadow, the line classes and the presets.

Key types and names: `EffectStack`, the ordered effects of one line class (at most one casing,
one glow and one shadow, all from `pyntpot.ink`); `LINE_CLASSES`, the eight classes a stack can
be set on, the basemap's seven and `route`; `WATER_GROUP` and `ROAD_GROUP`, the basemap classes in
the order the painter draws them; `BUILT_IN_PRESETS`, the three effect presets the package ships,
`cased`, `halo` and `lifted`; `checked_line_effects`, which the basemap group runs on its table.

A stack's widths are in display pixels; the compose and paint steps scale them to the array they
lay the stack on. An effect is off at a strength of 0, or, for a casing, a width of 0 (`-0.0`
included). A stack drops its off effects when it is built, so a stack written all off equals
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

from pyntpot.ink import Casing, Glow, Shadow
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.naming import nearest

#: The basemap's line classes in painting order: the water group, then the road group.
_BASEMAP = tuple(BrushStyle().brushes)

#: The water classes, in the order the painter draws them.
WATER_GROUP: tuple[str, ...] = _BASEMAP[:4]

#: The road classes, in the order the painter draws them.
ROAD_GROUP: tuple[str, ...] = _BASEMAP[4:]

#: Every class a stack can be set on: the seven basemap classes and the route.
LINE_CLASSES: frozenset[str] = frozenset(_BASEMAP) | {"route"}


def _is_off(effect: Casing | Glow | Shadow) -> bool:
    """Whether `effect` draws nothing: a strength of 0, or, for a casing, a width of 0."""
    if effect.strength == 0:
        return True
    return isinstance(effect, Casing) and effect.width_px == 0


@dataclass(frozen=True, kw_only=True)
class EffectStack:
    """The ordered effects of one line class: at most one casing, one glow and one shadow.

    Attributes:
        effects: The effects in the order they are applied, none off; an off effect is dropped
            when the stack is built.
    """

    effects: tuple[Casing | Glow | Shadow, ...] = ()

    def __post_init__(self) -> None:
        """Refuse two effects of a kind, drop the off ones and hold the rest as a tuple.

        Raises:
            ValueError: When two effects are of one kind.
            TypeError: When an effect is no `Casing`, `Glow` or `Shadow`.
        """
        kept: list[Casing | Glow | Shadow] = []
        seen: set[type] = set()
        for effect in self.effects:
            if not isinstance(effect, Casing | Glow | Shadow):
                raise TypeError(f"{effect!r} is not a Casing, Glow or Shadow")
            if type(effect) in seen:
                raise ValueError(f"a stack takes at most one {type(effect).__name__.lower()}")
            seen.add(type(effect))
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
    hint = "".join(f"; did you mean {name}?" for name in nearest(key, known))
    return (
        f"line_effects key {key!r} is not a basemap line class{hint}; "
        f"the classes are {', '.join(known)}"
    )
