"""API endpoints: upload, crop, process, preview, PDF download."""

import asyncio
import logging
import re
import shutil
import time
import uuid
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from src.api.schemas import (
    CropRequest,
    CropResponse,
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
from src.models.mosaic import MosaicSheet
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
    """
    img = Image.open(BytesIO(data))
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
    """Get the temp directory for an image ID."""
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
    return CropResponse(
        cropped_image_id=cropped_id, width=cropped.width, height=cropped.height
    )


def _run_pipeline(
    img: Image.Image, num_colors: int, size: int = 3, mode: str = "square"
) -> tuple[MosaicSheet, Image.Image, list[dict]]:
    """Run the CPU-intensive processing pipeline synchronously.

    Args:
        img: Input image.
        num_colors: Number of colors for quantization.
        size: Component size in mm (3, 4, or 5).
        mode: Mosaic mode ('square', 'circle', or 'hexagon').

    Returns:
        Tuple of (mosaic_sheet, preview_image, palette_info).
    """
    t0 = time.monotonic()

    columns, rows = GRID_DIMENSIONS[(size, mode)]

    # Enhance
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

    # Build palette info
    palette_info = []
    for i in range(palette.count):
        palette_info.append(
            {
                "index": i,
                "label": palette.label(i),
                "hex": palette.hex_color(i),
            }
        )

    logger.info("Pipeline complete: mosaic_id=%s total=%.2fs", mosaic_id, t4 - t0)
    return sheet, preview_img, palette_info


@router.post("/process", response_model=ProcessResponse)
async def process_image(req: ProcessRequest) -> ProcessResponse:
    """Run the full processing pipeline: enhance → quantize → grid → preview."""
    _validate_id(req.cropped_image_id, "cropped image ID")
    logger.info(
        "Processing image %s with %d colors", req.cropped_image_id, req.num_colors
    )

    img = _load_stored_image(req.cropped_image_id)

    sheet, preview_img, palette_info = await asyncio.to_thread(
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
        raise HTTPException(
            status_code=404, detail=f"Preview for '{mosaic_id}' not found"
        )
    return Response(
        content=preview_path.read_bytes(),
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
        headers={
            "Content-Disposition": f'attachment; filename="mosaic-{mosaic_id[:8]}.pdf"'
        },
    )
