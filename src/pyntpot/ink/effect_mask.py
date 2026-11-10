"""The line threshold and its check, shared by every effect primitive.

Key names: `LINE_THRESHOLD`, the mask value at which a pixel counts as the line (0.3), the
default of every primitive's `threshold` keyword, and `check_threshold`.

It draws nothing. Invariant: a threshold is above 0, because the shadow divides by it.
"""

LINE_THRESHOLD = 0.3


def check_threshold(threshold: float) -> None:
    """Refuse a threshold that is not above 0.

    Args:
        threshold: The mask value at which a pixel counts as the line.

    Raises:
        ValueError: Naming `threshold`, when it is 0, negative or not a number.
    """
    if not threshold > 0:
        raise ValueError(f"threshold must be above 0; got {threshold!r}")
