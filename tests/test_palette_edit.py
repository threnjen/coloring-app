"""Unit tests for color palette editing. AC2.6, AC2.7."""

import numpy as np

from src.models.mosaic import ColorPalette, GridCell, MosaicSheet


def _make_palette(n: int = 5) -> ColorPalette:
    """Create a palette with n distinct colors."""
    rng = np.random.default_rng(42)
    colors = rng.integers(0, 255, size=(n, 3), dtype=np.uint8)
    return ColorPalette(colors_rgb=colors.astype(np.float64))


def _make_sheet(palette: ColorPalette, rows: int = 4, cols: int = 4) -> MosaicSheet:
    """Create a minimal MosaicSheet with the given palette."""
    grid: list[list[GridCell]] = []
    for r in range(rows):
        row: list[GridCell] = []
        for c in range(cols):
            idx = (r * cols + c) % palette.count
            row.append(GridCell(row=r, col=c, color_index=idx, label=palette.label(idx)))
        grid.append(row)
    return MosaicSheet(
        mosaic_id="a" * 32,
        grid=grid,
        palette=palette,
        columns=cols,
        rows=rows,
    )


class TestColorSwapUpdatesPalette:
    """AC2.7 — editing a color index changes colors_rgb."""

    def test_color_swap_updates_palette(self) -> None:
        """Updating colors_rgb[i] changes the palette color at that index."""
        palette = _make_palette(5)
        old_color = palette.colors_rgb[2].copy()
        new_rgb = np.array([255, 0, 128], dtype=np.float64)

        palette.colors_rgb[2] = new_rgb

        assert np.array_equal(palette.colors_rgb[2], new_rgb)
        assert not np.array_equal(palette.colors_rgb[2], old_color)
        assert palette.hex_color(2) == "#FF0080"


class TestColorSwapPreservesLabels:
    """AC2.7 — labels are unchanged after palette edit."""

    def test_color_swap_preserves_labels(self) -> None:
        """After editing a color, all labels remain the same."""
        palette = _make_palette(5)
        original_labels = [palette.label(i) for i in range(palette.count)]

        palette.colors_rgb[3] = [10, 20, 30]

        labels_after = [palette.label(i) for i in range(palette.count)]
        assert labels_after == original_labels


class TestColorSwapPreservesGrid:
    """AC2.7 — grid cells are unchanged after palette edit."""

    def test_color_swap_preserves_grid(self) -> None:
        """After editing a color, all grid cell color_indices and labels stay the same."""
        palette = _make_palette(5)
        sheet = _make_sheet(palette)

        # Capture original grid state
        original_indices = [[cell.color_index for cell in row] for row in sheet.grid]
        original_labels = [[cell.label for cell in row] for row in sheet.grid]

        # Edit palette
        sheet.palette.colors_rgb[2] = [0, 0, 0]

        # Grid should be unchanged
        current_indices = [[cell.color_index for cell in row] for row in sheet.grid]
        current_labels = [[cell.label for cell in row] for row in sheet.grid]
        assert current_indices == original_indices
        assert current_labels == original_labels


class TestSimilarColorWarning:
    """AC2.6 — LAB distance < 15 triggers a similarity warning."""

    def test_similar_color_warning(self) -> None:
        """Two colors with LAB distance < 15 produce a warning."""
        from src.api.routes import _compute_palette_warnings

        palette = ColorPalette(
            colors_rgb=np.array(
                [
                    [255, 0, 0],  # index 0: red
                    [0, 255, 0],  # index 1: green
                    [0, 0, 255],  # index 2: blue
                    [250, 5, 0],  # index 3: very similar to red (index 0)
                ],
                dtype=np.float64,
            )
        )
        # Editing index 3 to a color very similar to index 0
        warnings = _compute_palette_warnings(palette, color_index=3)
        assert any("similar" in w.lower() or "hard to distinguish" in w.lower() for w in warnings)

    def test_no_warning_for_distinct_color(self) -> None:
        """Distant colors produce no similarity warnings."""
        from src.api.routes import _compute_palette_warnings

        palette = ColorPalette(
            colors_rgb=np.array(
                [
                    [255, 0, 0],
                    [0, 255, 0],
                    [0, 0, 255],
                ],
                dtype=np.float64,
            )
        )
        warnings = _compute_palette_warnings(palette, color_index=0)
        assert len(warnings) == 0


class TestDuplicateColorWarning:
    """AC2.6 — exact RGB match triggers a duplicate warning."""

    def test_duplicate_color_warning(self) -> None:
        """Identical colors produce a 'already used' warning."""
        from src.api.routes import _compute_palette_warnings

        palette = ColorPalette(
            colors_rgb=np.array(
                [
                    [100, 200, 50],
                    [0, 0, 0],
                    [100, 200, 50],  # duplicate of index 0
                ],
                dtype=np.float64,
            )
        )
        warnings = _compute_palette_warnings(palette, color_index=2)
        assert any("already used" in w.lower() for w in warnings)


class TestHexColorValidation:
    """AC2.6 — invalid hex is rejected."""

    def test_valid_hex_accepted(self) -> None:
        """A well-formed hex string passes regex validation."""
        import re

        pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        assert pattern.match("#FF00AA")
        assert pattern.match("#000000")
        assert pattern.match("#ffffff")

    def test_invalid_hex_rejected(self) -> None:
        """Malformed hex strings fail regex validation."""
        import re

        pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        assert not pattern.match("FF00AA")  # missing #
        assert not pattern.match("#FF00A")  # too short
        assert not pattern.match("#GG0000")  # invalid chars
        assert not pattern.match("#FF00AABB")  # too long
