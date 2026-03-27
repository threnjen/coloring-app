# 01: Component Size Selector — Context

## Key Files

| File | Role | Key Symbols |
|------|------|-------------|
| `src/config.py` | Constants: `COMPONENT_SIZE_MM`, `GRID_COLUMNS`, `GRID_ROWS`, paper dimensions | Currently hardcoded to 3mm/60/80 |
| `src/processing/grid.py` | `GridGenerator.__init__(columns, rows)` — already parameterized | `generate()` downsamples label map to grid |
| `src/rendering/pdf.py` | `PdfRenderer._draw_grid_page()` — reads `sheet.component_size_mm`, `sheet.columns`, `sheet.rows` | Margin calc uses `MARGIN_SIDE_MM`, `MARGIN_TOP_MM` from config |
| `src/rendering/preview.py` | `PreviewRenderer.render()` — derives dimensions from grid shape | Cell size is `PREVIEW_CELL_PX` (12px), independent of mm size |
| `src/models/mosaic.py` | `MosaicSheet` dataclass — carries `component_size_mm`, `columns`, `rows` | Already has the fields; just needs correct values passed in |
| `src/api/routes.py` | `_run_pipeline()` — constructs `GridGenerator(columns=GRID_COLUMNS, rows=GRID_ROWS)` | Needs to look up dimensions by size |
| `src/api/schemas.py` | `ProcessRequest` — currently only has `cropped_image_id` and `num_colors` | Needs `size` field |
| `static/js/app.js` | Process button handler — sends `cropped_image_id` + `num_colors` | Needs to include `size` |
| `static/index.html` | Step 3 "Choose Colors" section | Needs size dropdown |
| `tests/test_grid.py` | `test_grid_dimensions_3mm` — verifies 60×80 | Needs 4mm and 5mm variants |

## Key Decisions

1. **Lookup table over formula**: Grid dimensions are defined as explicit values in a lookup dict, not computed at runtime. This matches the spec exactly and avoids floating-point rounding surprises.

2. **Hexagon dimensions defined here, rendered in 02**: The lookup table includes hexagon entries `(size, "hexagon")` even though hexagon rendering doesn't exist yet. This avoids a config change in feature 02.

3. **Backward compatibility**: The existing `COMPONENT_SIZE_MM`, `GRID_COLUMNS`, `GRID_ROWS` constants remain as defaults. Existing tests that use them continue to pass unchanged.

4. **Mode key in lookup table uses string, not enum**: The lookup key uses `"square"` / `"circle"` / `"hexagon"` strings. The `MosaicMode` enum is added in 02-mosaic-modes. Using strings here avoids adding mode concepts prematurely. Circle maps to the same dimensions as square.

## Constraints

- Paper is US Letter (215.9mm × 279.4mm)
- Printable area baseline: 180mm × 240mm (from 3mm × 60×80)
- For 4mm and 5mm, printable area can grow slightly since the grid fills more of the page
- PDF margins = `(paper_dimension - grid_dimension) / 2`

## Grid Dimension Reference

### Square / Circle

| Size | Columns | Rows | Grid Width | Grid Height | Side Margin | Top Margin |
|------|---------|------|------------|-------------|-------------|------------|
| 3mm  | 60      | 80   | 180mm      | 240mm       | 17.95mm     | 19.7mm     |
| 4mm  | 50      | 65   | 200mm      | 260mm       | 7.95mm      | 9.7mm      |
| 5mm  | 40      | 52   | 200mm      | 260mm       | 7.95mm      | 9.7mm      |

### Hexagon (pointy-top)

| Size | Columns | Rows | Col Spacing | Row Spacing | Grid Width | Grid Height |
|------|---------|------|-------------|-------------|------------|-------------|
| 3mm  | 60      | 93   | 3mm         | 2.60mm      | 180mm      | ~241.8mm    |
| 4mm  | 45      | 70   | 4mm         | 3.46mm      | 180mm      | ~242.2mm    |
| 5mm  | 36      | 56   | 5mm         | 4.33mm      | 180mm      | ~242.5mm    |
