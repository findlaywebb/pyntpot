"""The pigment registry and the one lookup, `pigment`.

Key types: `PigmentRegistry`, a read-only set of pigments keyed by canonical name; `PIGMENT_REGISTRY`,
the shared registry of the 25 shipped pigments; `pigment`, which turns a `Pigment`, a name or a
`#rrggbb` into a `Pigment`.

It holds no aliases and reads no theme: adding pigments returns a new registry and never changes
the shared one. `PigmentRegistry.get` is the only place a miss message is written.

Invariants: a registry holds one pigment per name, in the order given.
"""

from dataclasses import dataclass
from functools import cached_property

from pyntpot.ink.colour import Colour
from pyntpot.ink.naming import nearest
from pyntpot.ink.pigment_table import ROLE_PIGMENTS, TUBE_PIGMENTS, Pigment


@dataclass(frozen=True)
class PigmentRegistry:
    """A read-only set of pigments, each looked up by its name.

    Attributes:
        pigments: Every pigment, in registry order, one per name.
    """

    pigments: tuple[Pigment, ...]

    def __post_init__(self) -> None:
        """Refuse two pigments of one name.

        Raises:
            ValueError: When a name appears twice.
        """
        seen: set[str] = set()
        for p in self.pigments:
            if p.name in seen:
                raise ValueError(f"duplicate pigment {p.name!r}")
            seen.add(p.name)

    @cached_property
    def _index(self) -> dict[str, Pigment]:
        return {p.name: p for p in self.pigments}

    def names(self) -> tuple[str, ...]:
        """Every canonical name, in registry order."""
        return tuple(self._index)

    def get(self, name: str) -> Pigment:
        """The pigment called `name`.

        Args:
            name: A canonical pigment name.

        Returns:
            The registered pigment.

        Raises:
            ValueError: When no pigment has the name; the message names the nearest one.
        """
        found = self._index.get(name)
        if found is not None:
            return found
        near = nearest(name, self._index)
        hint = f"; did you mean {near[0]}?" if near else ""
        raise ValueError(f"no pigment {name!r}{hint}")

    def __contains__(self, name: object) -> bool:
        """Whether a pigment has the name."""
        return name in self._index

    def extended(self, added: tuple[Pigment, ...]) -> "PigmentRegistry":
        """A new registry of these pigments followed by `added`; this one is unchanged.

        Args:
            added: Pigments to add after the existing ones.

        Returns:
            The extended registry.

        Raises:
            ValueError: When an added name is already in the registry or repeats.
        """
        return PigmentRegistry((*self.pigments, *added))


PIGMENT_REGISTRY = PigmentRegistry((*ROLE_PIGMENTS, *TUBE_PIGMENTS))
"""The 25 shipped pigments: the fifteen a map names by role, then the ten a painter names by tube."""


def pigment(ref: str | Pigment, registry: PigmentRegistry | None = None) -> Pigment:
    """The one pigment lookup: a pigment, a canonical name or a `#rrggbb`.

    Args:
        ref: A `Pigment` (returned as itself), a canonical name, or a `#rrggbb` in either case
            (an anonymous pigment named by the lower-case hex, with no transparency or Colour
            Index code).
        registry: Where a name is looked up; the shared `PIGMENT_REGISTRY` when `None`.

    Returns:
        The pigment.

    Raises:
        ValueError: When a name is not in the registry (the message names the nearest), or a
            `#` reference is not six hexadecimal digits.
    """
    if isinstance(ref, Pigment):
        return ref
    if ref.startswith("#"):
        colour = Colour.parse(ref)
        return Pigment(name=str(colour), colour=colour, transparency=None, colour_index=None)
    return (PIGMENT_REGISTRY if registry is None else registry).get(ref)
