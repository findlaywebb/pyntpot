"""One name, once: dropping a label that repeats another's name or place.

Key names: `dedupe_names`, the labels that survive when two name one place; `_stem`,
`_words` and `_one_place`, how two names are judged to be the same place;
`NAME_FAMILY` and `NAME_ALLOWANCE`, how many of a family one card keeps.

It does not place a name or choose its tier.

Invariants: a place is named at most the allowance of its family, and a leading
qualifier (`QUALIFIERS`) is ignored, so Upper and Lower Swell are one place.
"""

import logging
import math
import re

from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_SPAN, Label

log = logging.getLogger(__name__)


#: The qualifiers a pair of settlements is split by. Upper and Lower Swell
#: are one place to the person riding through them, and are called by their
#: stem.
QUALIFIERS = (
    "Upper",
    "Lower",
    "Great",
    "Little",
    "Nether",
    "Over",
    "North",
    "South",
    "East",
    "West",
    "New",
    "Old",
)


def _stem(name: str) -> str:
    """A settlement name without its leading qualifier."""
    return re.sub(rf"^({'|'.join(QUALIFIERS)})\s+", "", str(name)).strip()


#: How many times the major watercourse carries its own name. Two, and only the
#: major one: a river crossing the whole map is read in pieces, and a reader
#: who meets it at the bottom of the card should not have to trace it to the top
#: to find out what it is. This is ordinary cartographic practice for a long
#: feature. Every other watercourse gets
#: one, because a tributary that runs a third of the card twice-named is
#: repetition rather than help.
MAJOR_RIVER_LABELS = 2


#: Which repeat family each kind of name is counted in. Families never see each
#: other, because the answer is different in each: the major watercourse is
#: deliberately lettered twice, a road number once, and a place exactly once
#: however many pools found it. A guard that were one number for the whole
#: map would either letter the Eden once or letter Elm twice.
NAME_FAMILY = {"river": "water", "road": "road"}


#: What everything that is a point on the ground counts in. A settlement, a
#: user's own place and a landmark all name somewhere a reader goes, and
#: they come from three different pools that have never known about each other:
#: "Elm" can arrive as a settlement and again as the nearest named feature,
#: and "Bakewell" can do the same.
NAME_FAMILY_DEFAULT = "place"


#: How many times one name may be lettered inside its own family.
NAME_ALLOWANCE = {"water": MAJOR_RIVER_LABELS}


NAME_ALLOWANCE_DEFAULT = 1


#: How near two names have to be on the ground before they can be one place, in
#: metres. Stated in metres and not in pixels because "basically the same
#: place" is a fact about the ground rather than about the map: High Cup Nick
#: and High Cup Nick Cairn are five metres apart and are one headland, which
#: is a pixel on that card and would be a fifth of a pixel on a ride's, and
#: neither number says anything a rule can be built on.
NEAR_DUPLICATE_M = 150.0


#: How many words the longer name may add to the shorter one, at most, and
#: still be two names for one thing. The string relationship alone is
#: not enough and neither is the distance: Braemar and Braemar War Memorial
#: stand in the same word relationship as High Cup Nick and its chimney and are
#: a town and a monument in it, and they are told apart by being 485 m apart
#: rather than five. Both tests have to pass.
NEAR_DUPLICATE_EXTRA_WORDS = 2


def _words(name: str) -> list[str]:
    """A name as comparable words: case folded, unpunctuated, unqualified."""
    plain = re.sub(r"[^\w\s]", " ", _stem(str(name)))
    return plain.casefold().split()


def _one_place(a: str, b: str) -> bool:
    """Whether one name is the other with a few words added at either end.

    Whole words only. "High Cup Nick Cairn" is "High Cup Nick" and a thing on
    it; "High Cup Nicks" is not, and a character-wise prefix test cannot say so.
    """
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    short, whole = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    extra = len(whole) - len(short)
    if extra > NEAR_DUPLICATE_EXTRA_WORDS:
        return False
    return whole[: len(short)] == short or whole[extra:] == short


def dedupe_names(labels: list[Label], card: Card) -> list[Label]:
    """One name a place, and one name for a place, in the caller's own order.

    Two rules, and they are the same rule at two distances.

    A name repeated exactly is lettered once inside its family, wherever the
    two anchors are: a settlement named at both ends of the map is still one
    settlement. The major watercourse is the deliberate exception and carries
    its allowance in `NAME_ALLOWANCE`, which is why the guard is per family and
    not global.

    A name that contains another, within `NEAR_DUPLICATE_M` of it, is two names
    for one place and the map keeps one. Which one is not a judgement about
    fame: the tiers already rank what a name *is*, so the lower tier wins, and
    between two of the same tier the shorter and more general name does. That
    gives the village over the nearest-feature repeat of it, and the headland
    over the chimney standing on it.

    A span is never deduped. Its name is the caller's prose about a stretch
    of the session rather than a name for somewhere, and two stretches may
    fairly be called the same thing.

    Args:
        labels: The names, in the order the caller wants them back.
        card: The card, for the pixels-per-metre its distances are read in.

    Returns:
        The labels that survive, in the order they were given.
    """
    scale = max(float(getattr(card, "scale", 0.0)), 1e-9)
    order = sorted(labels, key=lambda lb: (lb.tier, len(str(lb.name))))
    kept: list[Label] = []
    used: dict[tuple[str, str], int] = {}
    for lb in order:
        if lb.tier == TIER_SPAN:
            kept.append(lb)
            continue
        family = NAME_FAMILY.get(lb.kind, NAME_FAMILY_DEFAULT)
        key = (family, " ".join(_words(lb.name)))
        allowance = NAME_ALLOWANCE.get(family, NAME_ALLOWANCE_DEFAULT)
        if used.get(key, 0) >= allowance:
            log.info("dropped a repeat of %r: %s carries %d already", lb.name, family, allowance)
            continue
        near = any(
            other.tier != TIER_SPAN
            and NAME_FAMILY.get(other.kind, NAME_FAMILY_DEFAULT) == family
            and " ".join(_words(other.name)) != key[1]
            and _one_place(other.name, lb.name)
            and math.dist((lb.px, lb.py), (other.px, other.py)) / scale <= NEAR_DUPLICATE_M
            for other in kept
        )
        if near:
            log.info("dropped %r: the sheet already names that place", lb.name)
            continue
        used[key] = used.get(key, 0) + 1
        kept.append(lb)
    keep = {id(lb) for lb in kept}
    return [lb for lb in labels if id(lb) in keep]
