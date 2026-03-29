"""API endpoints: upload, crop, process, preview, PDF download."""

import asyncio
import json
import logging
import re
import shutil
import time
import uuid
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response
from PIL import Image

from pydantic import ValidationError

from src.api.schemas import (
    BackgroundInfoSchema,
    BackgroundListResponse,
    CompositeRequest,
    CompositeResponse,
    CropRequest,
    CropResponse,
    CutoutRequest,
    CutoutResponse,
    PaletteEditRequest,
    PaletteEditResponse,
    ProcessRequest,
    ProcessResponse,
    UploadResponse,
)
from src.config import (
    GRID_DIMENSIONS,
    MAX_IMAGE_DIMENSION,
    MAX_UPLOAD_SIZE_BYTES,
    MIN_CROP_PIXELS,
    TEMP_DIR,
)
from src.models.mosaic import ColorPalette, MosaicSheet
from src.processing.backgrounds import BackgroundProvider
from src.processing.compositing import Compositor
from src.processing.cutout import CutoutProcessor
from src.processing.enhancement import ImageEnhancer
from src.processing.grid import GridGenerator
from src.processing.quantization import ColorQuantizer
from src.rendering.pdf import PdfRenderer
from src.rendering.preview import PreviewRenderer

logger = logging.getLogger(__name__)
router = APIRouter()

# Magic bytes for JPEG and PNG
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# In-memory store for mosaic sheets (Phase 1: no persistence)
_MAX_MOSAIC_STORE: int = 100
_mosaic_store: OrderedDict[str, MosaicSheet] = OrderedDict()

# Regex for validating hex UUID IDs
_UUID_HEX_RE = re.compile(r"^[a-f0-9]{32}$")


def _validate_id(value: str, name: str = "ID") -> None:
    """Validate that a value is a hex UUID.

    Raises:
        HTTPException: If the value is not a valid hex UUID.
    """
    if not _UUID_HEX_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {name}")


def _validate_image_bytes(data: bytes) -> str:
    """Validate that raw bytes are a real JPEG or PNG image.

    Args:
        data: Raw file bytes.

    Returns:
        Detected format string ('JPEG' or 'PNG').

    Raises:
        HTTPException: If the file is not a valid image.
    """
    if data[:3] == _JPEG_MAGIC:
        return "JPEG"
    if data[:8] == _PNG_MAGIC:
        return "PNG"
    raise HTTPException(status_code=400, detail="File is not a valid JPEG or PNG image")


def _load_image(data: bytes) -> Image.Image:
    """Load an image from bytes, converting RGBA to RGB with white background.

    Args:
        data: Raw image bytes.

    Returns:
        PIL Image in RGB mode.

    Raises:
        HTTPException: If the image data is corrupt or unreadable.
    """
    try:
        img = Image.open(BytesIO(data))
        img.load()  # Force decode to catch truncated/corrupt data
    except Exception as exc:
        logger.exception("Failed to load image data")
        raise HTTPException(status_code=400, detail="Could not read image") from exc
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        return background
    return img.convert("RGB")


def _resize_if_needed(img: Image.Image) -> Image.Image:
    """Resize image if it exceeds the max dimension.

    Args:
        img: PIL Image.

    Returns:
        Possibly resized PIL Image.
    """
    max_dim = max(img.width, img.height)
    if max_dim > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / max_dim
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        logger.info("Resizing %dx%d → %dx%d", img.width, img.height, new_w, new_h)
        return img.resize((new_w, new_h), Image.LANCZOS)
    return img


def _get_image_dir(image_id: str) -> Path:
    """Get the temp directory for an image ID.

    Defense-in-depth: validates the ID even though endpoint callers
    also call ``_validate_id``.  Raises ``ValueError`` (not
    ``HTTPException``) so misuse by internal code surfaces as a
    loud 500 rather than silently writing to an arbitrary path.

    Raises:
        ValueError: If image_id is not a valid hex UUID.
    """
    if not _UUID_HEX_RE.match(image_id):
        raise ValueError(f"Invalid image ID: {image_id!r}")
    return TEMP_DIR / image_id


def _save_image(image_id: str, img: Image.Image) -> Path:
    """Save an image to the temp directory."""
    img_dir = _get_image_dir(image_id)
    img_dir.mkdir(parents=True, exist_ok=True)
    path = img_dir / "image.png"
    img.save(str(path), "PNG")
    return path


def _load_stored_image(image_id: str) -> Image.Image:
    """Load a previously stored image by ID.

    Raises:
        HTTPException: If image not found.
    """
    path = _get_image_dir(image_id) / "image.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
    return Image.open(str(path)).convert("RGB")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile) -> UploadResponse:
    """Upload an image file (JPEG or PNG).

    Validates magic bytes, file size, and stores the image for further processing.
    """
    t0 = time.monotonic()

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
            )
        chunks.append(chunk)
    data = b"".join(chunks)

    _validate_image_bytes(data)
    img = _load_image(data)
    img = _resize_if_needed(img)

    image_id = uuid.uuid4().hex
    _save_image(image_id, img)

    logger.info(
        "Upload complete: id=%s size=%dx%d elapsed=%.2fs",
        image_id,
        img.width,
        img.height,
        time.monotonic() - t0,
    )
    return UploadResponse(image_id=image_id, width=img.width, height=img.height)


@router.get("/image/{image_id}")
async def get_image(image_id: str) -> Response:
    """Return the stored image for cropping (reflects any server-side resize)."""
    _validate_id(image_id, "image ID")
    path = _get_image_dir(image_id) / "image.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
    return Response(content=path.read_bytes(), media_type="image/png")


@router.post("/crop", response_model=CropResponse)
async def crop_image(req: CropRequest) -> CropResponse:
    """Crop an uploaded image to the specified region."""
    t0 = time.monotonic()
    _validate_id(req.image_id, "image ID")

    img = _load_stored_image(req.image_id)

    # Validate crop bounds
    if req.x + req.width > img.width or req.y + req.height > img.height:
        raise HTTPException(
            status_code=400,
            detail="Crop region exceeds image bounds",
        )
    if req.width < MIN_CROP_PIXELS or req.height < MIN_CROP_PIXELS:
        raise HTTPException(
            status_code=400,
            detail=f"Crop region too small. Minimum size is {MIN_CROP_PIXELS}×{MIN_CROP_PIXELS} pixels",
        )

    cropped = img.crop((req.x, req.y, req.x + req.width, req.y + req.height))
    cropped_id = uuid.uuid4().hex
    _save_image(cropped_id, cropped)

    logger.info(
        "Crop complete: id=%s size=%dx%d elapsed=%.2fs",
        cropped_id,
        cropped.width,
        cropped.height,
        time.monotonic() - t0,
    )
    return CropResponse(cropped_image_id=cropped_id, width=cropped.width, height=cropped.height)


def _run_pipeline(
    img: Image.Image, num_colors: int, size: int = 3, mode: str = "square"
) -> tuple[MosaicSheet, Image.Image, list[dict], Image.Image]:
    """Run the CPU-intensive processing pipeline synchronously.

    Args:
        img: Input image.
        num_colors: Number of colors for quantization.
        size: Component size in mm (3, 4, or 5).
        mode: Mosaic mode ('square', 'circle', or 'hexagon').

    Returns:
        Tuple of (mosaic_sheet, preview_image, palette_info, pre_enhance_image).
    """
    t0 = time.monotonic()

    try:
        columns, rows = GRID_DIMENSIONS[(size, mode)]
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported size/mode combination: size={size}, mode={mode}",
        ) from exc

    # Enhance — keep the pre-enhancement crop for before/after comparison
    pre_enhance_img = img.copy()
    enhancer = ImageEnhancer()
    enhanced = enhancer.enhance(img)
    t1 = time.monotonic()
    logger.info("Enhancement: %.2fs", t1 - t0)

    # Quantize
    quantizer = ColorQuantizer(n_colors=num_colors)
    label_map, palette = quantizer.quantize(enhanced)
    t2 = time.monotonic()
    logger.info("Quantization: %.2fs", t2 - t1)

    # Generate grid
    generator = GridGenerator(columns=columns, rows=rows)
    grid = generator.generate(label_map, palette)
    t3 = time.monotonic()
    logger.info("Grid generation: %.2fs", t3 - t2)

    # Build mosaic sheet
    mosaic_id = uuid.uuid4().hex
    sheet = MosaicSheet(
        mosaic_id=mosaic_id,
        grid=grid,
        palette=palette,
        columns=columns,
        rows=rows,
        component_size_mm=float(size),
        mode=mode,
    )

    # Render preview
    renderer = PreviewRenderer()
    preview_img = renderer.render(grid, palette, mode=mode)
    t4 = time.monotonic()
    logger.info("Preview rendering: %.2fs", t4 - t3)

    palette_info = _build_palette_info(palette)

    logger.info("Pipeline complete: mosaic_id=%s total=%.2fs", mosaic_id, t4 - t0)
    return sheet, preview_img, palette_info, pre_enhance_img


@router.post("/process", response_model=ProcessResponse)
async def process_image(req: ProcessRequest) -> ProcessResponse:
    """Run the full processing pipeline: enhance → quantize → grid → preview."""
    _validate_id(req.cropped_image_id, "cropped image ID")
    logger.info("Processing image %s with %d colors", req.cropped_image_id, req.num_colors)

    img = _load_stored_image(req.cropped_image_id)

    sheet, preview_img, palette_info, pre_enhance_img = await asyncio.to_thread(
        _run_pipeline, img, req.num_colors, req.size, req.mode.value
    )

    _mosaic_store[sheet.mosaic_id] = sheet
    while len(_mosaic_store) > _MAX_MOSAIC_STORE:
        evicted_id, _ = _mosaic_store.popitem(last=False)
        shutil.rmtree(_get_image_dir(evicted_id), ignore_errors=True)
        logger.info("Evicted mosaic %s and cleaned up disk files", evicted_id)

    preview_dir = _get_image_dir(sheet.mosaic_id)
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_img.save(str(preview_dir / "preview.png"), "PNG")

    # Save pre-enhancement crop at native resolution for before/after toggle
    pre_enhance_img.save(str(preview_dir / "pre_enhance.png"), "PNG")

    return ProcessResponse(
        mosaic_id=sheet.mosaic_id,
        num_colors=sheet.palette.count,
        columns=sheet.columns,
        rows=sheet.rows,
        component_size_mm=sheet.component_size_mm,
        mode=sheet.mode,
        palette=palette_info,
    )


@router.get("/preview/{mosaic_id}")
async def get_preview(mosaic_id: str) -> Response:
    """Return the preview PNG for a processed mosaic."""
    _validate_id(mosaic_id, "mosaic ID")
    preview_path = _get_image_dir(mosaic_id) / "preview.png"
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail=f"Preview for '{mosaic_id}' not found")
    return Response(
        content=preview_path.read_bytes(),
        media_type="image/png",
    )


@router.get("/preview/{mosaic_id}/original")
async def get_preview_original(mosaic_id: str) -> Response:
    """Return the pre-enhancement (original crop) preview PNG."""
    _validate_id(mosaic_id, "mosaic ID")
    original_path = _get_image_dir(mosaic_id) / "pre_enhance.png"
    if not original_path.exists():
        raise HTTPException(status_code=404, detail=f"Original preview for '{mosaic_id}' not found")
    return Response(
        content=original_path.read_bytes(),
        media_type="image/png",
    )


@router.get("/pdf/{mosaic_id}")
async def get_pdf(mosaic_id: str) -> Response:
    """Generate and return the PDF for a processed mosaic."""
    _validate_id(mosaic_id, "mosaic ID")
    sheet = _mosaic_store.get(mosaic_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail=f"Mosaic '{mosaic_id}' not found")

    t0 = time.monotonic()
    renderer = PdfRenderer()
    pdf_bytes = renderer.render(sheet)
    logger.info("PDF rendered: %d bytes (%.2fs)", len(pdf_bytes), time.monotonic() - t0)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="mosaic-{mosaic_id[:8]}.pdf"'},
    )


# --- Palette edit ---

_MIN_LAB_DISTANCE: float = 15.0


def _compute_palette_warnings(palette: ColorPalette, color_index: int) -> list[str]:
    """Check for duplicate or similar colors relative to the edited index.

    Args:
        palette: The palette (already updated with the new color).
        color_index: Index of the color that was just edited.

    Returns:
        List of warning strings (may be empty).
    """

    warnings: list[str] = []
    new_rgb = np.asarray(palette.colors_rgb[color_index], dtype=np.uint8)

    # Check exact duplicate first
    for i in range(palette.count):
        if i == color_index:
            continue
        other_rgb = np.asarray(palette.colors_rgb[i], dtype=np.uint8)
        if np.array_equal(new_rgb, other_rgb):
            warnings.append(f"This color is already used as label {palette.label(i)}")

    # Check LAB similarity — batch all colors into one conversion
    all_rgb = np.asarray(palette.colors_rgb, dtype=np.uint8)
    all_bgr = all_rgb[:, ::-1].reshape(1, -1, 3)
    all_lab = cv2.cvtColor(all_bgr, cv2.COLOR_BGR2LAB).astype(np.float64).reshape(-1, 3)
    new_lab = all_lab[color_index]

    for i in range(palette.count):
        if i == color_index:
            continue
        dist = np.linalg.norm(new_lab - all_lab[i])
        if dist < _MIN_LAB_DISTANCE and not np.array_equal(new_rgb, all_rgb[i]):
            warnings.append(
                f"Color {palette.label(color_index)} is very similar to "
                f"{palette.label(i)} — they may be hard to distinguish"
            )

    return warnings


def _build_palette_info(palette: ColorPalette) -> list[dict[str, object]]:
    """Build the palette info list for API responses."""
    return [
        {"index": i, "label": palette.label(i), "hex": palette.hex_color(i)}
        for i in range(palette.count)
    ]


@router.post("/palette/edit", response_model=PaletteEditResponse)
async def edit_palette(req: PaletteEditRequest) -> PaletteEditResponse:
    """Edit a single color in the palette and re-render the preview."""
    _validate_id(req.mosaic_id, "mosaic ID")

    sheet = _mosaic_store.get(req.mosaic_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail=f"Mosaic '{req.mosaic_id}' not found")

    palette = sheet.palette
    if req.color_index >= palette.count:
        raise HTTPException(
            status_code=400,
            detail=f"color_index {req.color_index} out of range [0, {palette.count})",
        )

    # Parse hex → RGB
    hex_str = req.new_color.lstrip("#")
    new_rgb = np.array(
        [int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)],
        dtype=np.uint8,
    )

    # Update palette in-place
    palette.colors_rgb[req.color_index] = new_rgb

    # Compute warnings
    warnings = _compute_palette_warnings(palette, req.color_index)

    # Re-render preview (CPU-bound + disk I/O — run off the event loop)
    # Snapshot palette colors to avoid race with concurrent edit_palette requests
    palette_snapshot = ColorPalette(colors_rgb=palette.colors_rgb.copy())

    def _render_and_save() -> None:
        renderer = PreviewRenderer()
        preview_img = renderer.render(sheet.grid, palette_snapshot, mode=sheet.mode)
        preview_dir = _get_image_dir(sheet.mosaic_id)
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_img.save(str(preview_dir / "preview.png"), "PNG")

    await asyncio.to_thread(_render_and_save)

    logger.info(
        "Palette edit: mosaic=%s index=%d new_color=%s warnings=%d",
        sheet.mosaic_id,
        req.color_index,
        req.new_color,
        len(warnings),
    )

    return PaletteEditResponse(
        palette=_build_palette_info(palette),
        warnings=warnings,
    )


# --- Phase 3: Image Editing ---


@router.post("/cutout", response_model=CutoutResponse)
async def cutout_image(req: CutoutRequest) -> CutoutResponse:
    """Remove background from a stored image, producing an RGBA cutout."""
    t0 = time.monotonic()
    _validate_id(req.image_id, "image ID")

    img = _load_stored_image(req.image_id)

    processor = CutoutProcessor()
    rgba, _mask = await asyncio.to_thread(processor.remove_background, img)

    cutout_id = uuid.uuid4().hex
    cutout_dir = _get_image_dir(cutout_id)
    cutout_dir.mkdir(parents=True, exist_ok=True)
    rgba.save(str(cutout_dir / "cutout.png"), "PNG")

    # Store reference to the original image for undo support
    (cutout_dir / "source_id.txt").write_text(req.image_id)

    logger.info(
        "Cutout complete: id=%s size=%dx%d elapsed=%.2fs",
        cutout_id,
        rgba.width,
        rgba.height,
        time.monotonic() - t0,
    )
    return CutoutResponse(cutout_image_id=cutout_id, width=rgba.width, height=rgba.height)


@router.get("/cutout/{cutout_id}/image")
async def get_cutout_image(cutout_id: str) -> Response:
    """Return the cutout RGBA PNG for frontend display."""
    _validate_id(cutout_id, "cutout ID")
    path = _get_image_dir(cutout_id) / "cutout.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Cutout '{cutout_id}' not found")
    return Response(content=path.read_bytes(), media_type="image/png")


@router.get("/backgrounds", response_model=BackgroundListResponse)
async def list_backgrounds() -> BackgroundListResponse:
    """Return list of available backgrounds (programmatic + file-based presets)."""
    provider = BackgroundProvider()
    backgrounds = provider.list_backgrounds()
    return BackgroundListResponse(
        backgrounds=[
            BackgroundInfoSchema(
                id=bg.id,
                name=bg.name,
                type=bg.type,
                thumbnail_url=None,
            )
            for bg in backgrounds
        ]
    )


@router.post("/composite", response_model=CompositeResponse)
async def composite_image(request: Request) -> CompositeResponse:
    """Composite a cutout onto a background.

    Accepts either:
    - JSON body with ``background_id`` for a preset background
    - Multipart form with ``background_file`` for a custom upload
    """
    t0 = time.monotonic()

    content_type = request.headers.get("content-type", "")
    background_file_data: bytes | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        cutout_image_id = form.get("cutout_image_id")
        background_id = form.get("background_id")
        try:
            x = int(form.get("x", 0))
            y = int(form.get("y", 0))
            scale = float(form.get("scale", 1.0))
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid numeric value for x, y, or scale: {exc}",
            ) from exc
        bg_file = form.get("background_file")
        if bg_file is not None:
            if not callable(getattr(bg_file, "read", None)):
                raise HTTPException(
                    status_code=400,
                    detail="background_file must be a file upload",
                )
            background_file_data = await bg_file.read()
    else:
        try:
            body = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON body: {exc}",
            ) from exc
        try:
            req = CompositeRequest.model_validate(body)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        cutout_image_id = req.cutout_image_id
        background_id = req.background_id
        x = req.x
        y = req.y
        scale = req.scale

    if not cutout_image_id:
        raise HTTPException(
            status_code=400,
            detail="cutout_image_id is required",
        )

    _validate_id(cutout_image_id, "cutout image ID")

    # Load cutout RGBA
    cutout_path = _get_image_dir(cutout_image_id) / "cutout.png"
    if not cutout_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Cutout '{cutout_image_id}' not found",
        )
    with Image.open(str(cutout_path)) as _cutout_img:
        subject = _cutout_img.convert("RGBA")
    crop_w, crop_h = subject.size

    # Load or generate background
    provider = BackgroundProvider()
    if background_file_data is not None:
        # Custom upload
        if len(background_file_data) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="Background file too large",
            )
        _validate_image_bytes(background_file_data)
        bg_img = _load_image(background_file_data)
        bg_img = provider.resize_to_fill(bg_img, crop_w, crop_h)
    elif background_id:
        bg_img = provider.get_background(background_id, crop_w, crop_h)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either background_id or background_file is required",
        )

    compositor = Compositor()
    result = await asyncio.to_thread(compositor.composite, subject, bg_img, x, y, scale)

    composite_id = uuid.uuid4().hex
    _save_image(composite_id, result)

    logger.info(
        "Composite complete: id=%s size=%dx%d bg=%s elapsed=%.2fs",
        composite_id,
        result.width,
        result.height,
        background_id or "custom-upload",
        time.monotonic() - t0,
    )
    return CompositeResponse(
        composite_image_id=composite_id, width=result.width, height=result.height
    )
