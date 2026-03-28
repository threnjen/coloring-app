"""Pydantic request/response models for the API."""

import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from src.config import MAX_COLORS, MIN_COLORS


class MosaicMode(str, Enum):
    """Available mosaic rendering modes."""

    SQUARE = "square"
    CIRCLE = "circle"
    HEXAGON = "hexagon"


class UploadResponse(BaseModel):
    """Response after uploading an image."""

    image_id: str
    width: int
    height: int


class CropRequest(BaseModel):
    """Request to crop an uploaded image."""

    image_id: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class CropResponse(BaseModel):
    """Response after cropping."""

    cropped_image_id: str
    width: int
    height: int


class ProcessRequest(BaseModel):
    """Request to process a cropped image into a mosaic."""

    cropped_image_id: str
    num_colors: int = Field(ge=MIN_COLORS, le=MAX_COLORS, default=12)
    size: int = Field(default=3, ge=3, le=5)
    mode: MosaicMode = MosaicMode.SQUARE


class PaletteEntry(BaseModel):
    """A single entry in the color palette."""

    index: int
    label: str
    hex: str


class ProcessResponse(BaseModel):
    """Response after processing into a mosaic."""

    mosaic_id: str
    num_colors: int
    columns: int
    rows: int
    component_size_mm: float
    mode: MosaicMode
    palette: list[PaletteEntry]


class PaletteEditRequest(BaseModel):
    """Request to edit a single color in the palette."""

    mosaic_id: str
    color_index: int = Field(ge=0)
    new_color: str

    @field_validator("new_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("new_color must be a hex string like '#FF00AA'")
        return v.upper()


class PaletteEditResponse(BaseModel):
    """Response after editing a palette color."""

    palette: list[PaletteEntry]
    warnings: list[str]


# --- Phase 3: Image Editing ---


class CutoutRequest(BaseModel):
    """Request to remove the background from an image."""

    image_id: str


class CutoutResponse(BaseModel):
    """Response after background removal."""

    cutout_image_id: str
    width: int
    height: int


class BackgroundInfoSchema(BaseModel):
    """Metadata for a single available background."""

    id: str
    name: str
    type: str
    thumbnail_url: str | None = None


class BackgroundListResponse(BaseModel):
    """Response listing all available backgrounds."""

    backgrounds: list[BackgroundInfoSchema]


class CompositeRequest(BaseModel):
    """Request to composite a cutout onto a background."""

    cutout_image_id: str
    background_id: str
    x: int = 0
    y: int = 0
    scale: float = Field(default=1.0, ge=0.25, le=2.0)


class CompositeResponse(BaseModel):
    """Response after compositing."""

    composite_image_id: str
    width: int
    height: int
