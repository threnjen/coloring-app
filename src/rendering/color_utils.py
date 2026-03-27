"""Shared color utilities for rendering modules."""


def perceived_brightness(r: float, g: float, b: float) -> float:
    """Compute perceived brightness using the ITU-R BT.601 luminance formula.

    The formula is linear, so it works at any scale (0–255 integer or
    0.0–1.0 float).  Callers must use a threshold consistent with
    the scale of their inputs.

    Args:
        r: Red component.
        g: Green component.
        b: Blue component.

    Returns:
        Weighted luminance in the same scale as the inputs.
    """
    return 0.299 * r + 0.587 * g + 0.114 * b
