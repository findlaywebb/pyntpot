"""A flat text measure: a fixed advance a character and a fixed line height.

The deterministic measure the unit tests place labels with, so a placement
expectation never depends on a font. It knows neither the face nor the size it
is asked about; the map itself always measures with the hand.
"""


def flat_measure(text: str, size: float) -> tuple[float, float]:
    """Return `(width, height)` in display pixels: 8 a character plus 8, by 20 tall.

    `size` is accepted and ignored.
    """
    return len(str(text)) * 8.0 + 8.0, 20.0
