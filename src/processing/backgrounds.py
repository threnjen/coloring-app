"""Background provider: programmatic solids/gradients and file-based presets."""

import logging
import re
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from src.config import PRESET_BACKGROUNDS_DIR

logger = logging.getLogger(__name__)

_VALID_PRESET_RE = re.compile(r"^[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$")


@dataclass
class BackgroundInfo:
    """Metadata for one available background."""

    id: str
    name: str
    type: str  # "programmatic" | "preset"
    colors: list[tuple[int, int, int]] = field(default_factory=list)


# Hard-coded registry of programmatic backgrounds
_PROGRAMMATIC_BACKGROUNDS: list[dict] = [
    # Solids
    {"id": "solid-white", "name": "White", "kind": "solid", "colors": [(255, 255, 255)]},
    {"id": "solid-light-gray", "name": "Light Gray", "kind": "solid", "colors": [(220, 220, 220)]},
    {"id": "solid-sky-blue", "name": "Sky Blue", "kind": "solid", "colors": [(135, 206, 235)]},
    {
        "id": "solid-pale-yellow",
        "name": "Pale Yellow",
        "kind": "solid",
        "colors": [(255, 255, 210)],
    },
    {"id": "solid-mint-green", "name": "Mint Green", "kind": "solid", "colors": [(189, 252, 201)]},
    {"id": "solid-light-pink", "name": "Light Pink", "kind": "solid", "colors": [(255, 182, 193)]},
    # Gradients (top, bottom)
    {
        "id": "gradient-blue-to-white",
        "name": "Blue to White",
        "kind": "gradient",
        "colors": [(70, 130, 180), (255, 255, 255)],
    },
    {
        "id": "gradient-sunset",
        "name": "Sunset",
        "kind": "gradient",
        "colors": [(255, 140, 0), (255, 105, 180)],
    },
    {
        "id": "gradient-forest",
        "name": "Forest",
        "kind": "gradient",
        "colors": [(34, 100, 34), (144, 238, 144)],
    },
]


class BackgroundProvider:
    """Provides programmatic and file-based preset backgrounds."""

    def list_backgrounds(self) -> list[BackgroundInfo]:
        """Return combined list of programmatic and file-based backgrounds."""
        result: list[BackgroundInfo] = []

        # Programmatic
        for entry in _PROGRAMMATIC_BACKGROUNDS:
            result.append(
                BackgroundInfo(
                    id=entry["id"],
                    name=entry["name"],
                    type="programmatic",
                    colors=entry["colors"],
                )
            )

        # File-based presets
        result.extend(self._scan_presets())
        return result

    def get_background(self, background_id: str, width: int, height: int) -> Image.Image:
        """Generate or load a background image at the requested dimensions.

        Args:
            background_id: ID of a programmatic or preset background.
            width: Target width in pixels.
            height: Target height in pixels.

        Returns:
            RGB Image at exactly (width, height).

        Raises:
            ValueError: If background_id is not found.
        """
        # Check programmatic
        for entry in _PROGRAMMATIC_BACKGROUNDS:
            if entry["id"] == background_id:
                if entry["kind"] == "solid":
                    return self._generate_solid(entry["colors"][0], width, height)
                else:
                    return self._generate_gradient(
                        entry["colors"][0], entry["colors"][1], width, height
                    )

        # Check file-based presets
        presets = self._scan_presets()
        for preset in presets:
            if preset.id == background_id:
                # Find the actual file (could be .png, .jpg, .jpeg)
                for ext in ("png", "jpg", "jpeg"):
                    candidate = PRESET_BACKGROUNDS_DIR / f"{preset.name}.{ext}"
                    if candidate.exists():
                        with Image.open(str(candidate)) as img:
                            img_rgb = img.convert("RGB")
                        return self.resize_to_fill(img_rgb, width, height)

        raise ValueError(f"Background '{background_id}' not found")

    @staticmethod
    def _generate_solid(color: tuple[int, int, int], width: int, height: int) -> Image.Image:
        """Generate a solid-color background."""
        return Image.new("RGB", (width, height), color)

    @staticmethod
    def _generate_gradient(
        color_top: tuple[int, int, int],
        color_bottom: tuple[int, int, int],
        width: int,
        height: int,
    ) -> Image.Image:
        """Generate a vertical linear gradient background."""
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):
            arr[:, :, c] = np.linspace(
                color_top[c], color_bottom[c], height, dtype=np.uint8
            ).reshape(-1, 1)
        return Image.fromarray(arr, "RGB")

    @staticmethod
    def resize_to_fill(img: Image.Image, width: int, height: int) -> Image.Image:
        """Scale-to-fill and center-crop an image to exact dimensions.

        Resizes preserving aspect ratio so the image fully covers the target
        area, then center-crops to the exact (width, height).
        """
        src_w, src_h = img.size
        scale = max(width / src_w, height / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return img.crop((left, top, left + width, top + height))

    @staticmethod
    def _scan_presets() -> list[BackgroundInfo]:
        """Scan the presets directory for valid image files."""
        presets: list[BackgroundInfo] = []
        if not PRESET_BACKGROUNDS_DIR.exists():
            return presets

        for path in sorted(PRESET_BACKGROUNDS_DIR.iterdir()):
            if not _VALID_PRESET_RE.match(path.name):
                continue
            stem = path.stem
            presets.append(
                BackgroundInfo(
                    id=f"preset-{stem}",
                    name=stem,
                    type="preset",
                )
            )
        return presets
