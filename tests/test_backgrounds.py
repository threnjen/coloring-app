"""Unit tests for BackgroundProvider (AC3.3, AC3.4)."""

import numpy as np
import pytest
from PIL import Image

from src.processing.backgrounds import BackgroundProvider


@pytest.fixture
def provider() -> BackgroundProvider:
    return BackgroundProvider()


@pytest.fixture
def preset_dir(tmp_path):
    """Create a temporary preset directory with sample images."""
    # Valid preset
    img = Image.new("RGB", (100, 100), (128, 64, 32))
    img.save(str(tmp_path / "sunset-photo.png"))
    img.save(str(tmp_path / "forest_01.jpg"))
    # Invalid filenames (should be rejected)
    img.save(str(tmp_path / "bad name.png"))
    img.save(str(tmp_path / "../traversal.png"))
    (tmp_path / "readme.txt").write_text("not an image")
    return tmp_path


class TestBackgroundProvider:
    """Tests for BackgroundProvider."""

    def test_programmatic_backgrounds_list(self, provider: BackgroundProvider) -> None:
        """AC3.3: Returns expected count — 6 solids + 3 gradients = 9."""
        backgrounds = provider.list_backgrounds()
        programmatic = [b for b in backgrounds if b.type == "programmatic"]
        assert len(programmatic) == 9
        # All have required fields
        for bg in programmatic:
            assert bg.id
            assert bg.name
            assert bg.type == "programmatic"

    def test_programmatic_solid_generates_correct_color(self, provider: BackgroundProvider) -> None:
        """AC3.3: White solid background pixels are all (255, 255, 255)."""
        bg = provider.get_background("solid-white", 100, 80)
        assert bg.mode == "RGB"
        arr = np.array(bg)
        assert np.all(arr == 255)

    def test_programmatic_gradient_has_color_range(self, provider: BackgroundProvider) -> None:
        """AC3.3: Gradient top and bottom rows differ."""
        bg = provider.get_background("gradient-blue-to-white", 100, 200)
        arr = np.array(bg)
        top_row = arr[0, :, :]
        bottom_row = arr[-1, :, :]
        assert not np.array_equal(top_row, bottom_row), "Gradient top/bottom should differ"

    def test_background_dimensions_match_request(self, provider: BackgroundProvider) -> None:
        """AC3.3: Output matches requested width x height."""
        bg = provider.get_background("solid-white", 300, 200)
        assert bg.size == (300, 200)

        bg2 = provider.get_background("gradient-sunset", 150, 400)
        assert bg2.size == (150, 400)

    def test_preset_file_backgrounds(self, preset_dir, monkeypatch) -> None:
        """AC3.3: File-based presets discovered from directory."""
        monkeypatch.setattr("src.processing.backgrounds.PRESET_BACKGROUNDS_DIR", preset_dir)
        provider = BackgroundProvider()
        backgrounds = provider.list_backgrounds()
        presets = [b for b in backgrounds if b.type == "preset"]
        # Only valid filenames should pass: sunset-photo.png, forest_01.jpg
        assert len(presets) == 2
        names = {b.name for b in presets}
        assert "sunset-photo" in names
        assert "forest_01" in names

    def test_preset_filename_validation(self, preset_dir, monkeypatch) -> None:
        """Security: Rejects files with invalid names (spaces, path traversal)."""
        monkeypatch.setattr("src.processing.backgrounds.PRESET_BACKGROUNDS_DIR", preset_dir)
        provider = BackgroundProvider()
        backgrounds = provider.list_backgrounds()
        preset_names = [b.name for b in backgrounds if b.type == "preset"]
        # These should NOT appear
        assert "bad name" not in preset_names
        assert "../traversal" not in preset_names
        assert "readme" not in preset_names

    def test_custom_bg_resized_to_fill(self, provider: BackgroundProvider) -> None:
        """AC3.4: Small bg scaled up, large bg center-cropped to fill."""
        # Small background (50x50) → should scale up to fill 200x100
        small = Image.new("RGB", (50, 50), (100, 100, 200))
        result = provider.resize_to_fill(small, 200, 100)
        assert result.size == (200, 100)

        # Large background (800x600) → should center-crop to 200x100
        large = Image.new("RGB", (800, 600), (100, 100, 200))
        result2 = provider.resize_to_fill(large, 200, 100)
        assert result2.size == (200, 100)
