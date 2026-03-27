"""Geometry helpers for mosaic shape rendering."""

import math


def hex_vertices(cx: float, cy: float, circumradius: float) -> list[tuple[float, float]]:
    """Compute the 6 vertices of a pointy-top regular hexagon.

    Args:
        cx: Center x coordinate.
        cy: Center y coordinate.
        circumradius: Distance from center to vertex (circumradius).

    Returns:
        List of 6 (x, y) tuples starting from the top vertex, going clockwise.
    """
    vertices = []
    for i in range(6):
        angle_deg = 60 * i - 90  # Start at top (-90°), go clockwise
        angle_rad = math.radians(angle_deg)
        x = cx + circumradius * math.cos(angle_rad)
        y = cy + circumradius * math.sin(angle_rad)
        vertices.append((x, y))
    return vertices
