# 02: Mosaic Modes — Context

## Key Files

| File | Role | Key Symbols |
|------|------|-------------|
| `src/rendering/preview.py` | `PreviewRenderer.render()` — currently draws rectangles only | Will add `_draw_square_cell`, `_draw_circle_cell`, `_draw_hexagon_cell` |
| `src/rendering/pdf.py` | `PdfRenderer._draw_grid_page()` — currently draws rects + labels | Will add per-mode cell drawing methods |
| `src/rendering/pdf.py` | `PdfRenderer._draw_legend_page()` — draws swatches + labels | Mode-independent; no changes expected |
| `src/models/mosaic.py` | `MosaicSheet` dataclass | Add `mode: str = "square"` field |
| `src/processing/grid.py` | `GridGenerator` — produces 2D `GridCell` array | Not changed — grid data is shape-independent |
| `src/api/schemas.py` | `ProcessRequest`, `ProcessResponse` | Add `MosaicMode` enum, `mode` field |
| `src/api/routes.py` | `_run_pipeline()` — orchestrates pipeline | Pass mode through; use for dimension lookup + rendering |
| `src/config.py` | `GRID_DIMENSIONS` lookup (from 01) | Lookup keyed by `(size, mode)` |
| `static/js/app.js` | Process handler | Add mode to request body |
| `static/index.html` | Step 3 section | Add mode toggle UI |

## Key Decisions

1. **Rendering-only change**: The `GridGenerator` and `ColorQuantizer` are shape-agnostic. A `GridCell` at position (r, c) with color_index N is valid regardless of whether it's rendered as a square, circle, or hexagon. Only the rendering layer changes.

2. **No separate grid files**: The Phase 2 spec proposed `rendering/grid_square.py`, `rendering/grid_circle.py`, `rendering/grid_hexagon.py`. This plan keeps rendering in `preview.py` and `pdf.py` because:
   - The logic is small (one method per shape per renderer)
   - Splitting would duplicate the cell iteration loop
   - Co-locating shape drawing with its renderer context (PIL Draw vs reportlab Canvas) is cleaner

3. **Shared geometry helper**: Hex vertex computation is needed in both preview and PDF. A small `src/rendering/geometry.py` module with `hex_vertices(cx, cy, size)` avoids duplication.

4. **Black background strategy**: For circle and hexagon modes, the entire grid area gets a black background fill first, then shapes are drawn on top. This naturally creates the black inter-cell space without drawing individual gaps.

5. **Circle uses square grid dimensions**: A circle inscribed in a square cell has the same spatial footprint. The dimension lookup for `"circle"` returns the same values as `"square"`.

## Hexagon Geometry Reference (Pointy-Top)

```
     *          ← top vertex (angle 0°)
    / \
   /   \        flat-to-flat = d (component_size - gap)
  *     *       vertex-to-vertex = d × 2/√3
  |     |
  *     *       col spacing = component_size
   \   /        row spacing = component_size × √3/2
    \ /
     *          ← bottom vertex (angle 180°)
```

Offset coordinate system:
- Even rows (0, 2, 4, ...): x = col × col_spacing
- Odd rows (1, 3, 5, ...): x = col × col_spacing + col_spacing / 2

6 vertices for pointy-top at center (cx, cy) with circumradius R = d / √3:
- (cx, cy - R)           — top
- (cx + R×cos(30°), cy - R×sin(30°))  — top-right
- (cx + R×cos(30°), cy + R×sin(30°))  — bottom-right
- (cx, cy + R)           — bottom
- (cx - R×cos(30°), cy + R×sin(30°))  — bottom-left
- (cx - R×cos(30°), cy - R×sin(30°))  — top-left

## Constraints

- reportlab `Canvas` supports: `rect()`, `circle()`, `beginPath()`/`moveTo()`/`lineTo()`/`closePath()`/`fillPath()`
- PIL `ImageDraw` supports: `rectangle()`, `ellipse()`, `polygon()`
- Both have text centering via bounding box calculation
- Font sizing must account for the inscribed circle of each shape (smallest for hexagon)
