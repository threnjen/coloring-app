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


class ProcessResponse(BaseModel):
    """Response after processing into a mosaic."""

    mosaic_id: str
    num_colors: int
    columns: int
    rows: int
    component_size_mm: float
    mode: MosaicMode
    palette: list[dict]


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

    palette: list[dict]
    warnings: list[str]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
