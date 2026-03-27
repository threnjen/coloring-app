"""Shared color utilities for rendering modules."""


def perceived_brightness(r: float, g: float, b: float) -> float:
    """Compute perceived brightness using the ITU-R BT.601 luminance formula.

    Args:
        r: Red component (0–255).
        g: Green component (0–255).
        b: Blue component (0–255).

    Returns:
        Perceived brightness (0.0–255.0).
    """
    return 0.299 * r + 0.587 * g + 0.114 * b
