from datetime import datetime
from pathlib import Path

from PIL import Image

from core.models import AppSettings
from core.watermark import apply_date_watermark


def test_apply_date_watermark_changes_pixels(tmp_path: Path):
    image_path = tmp_path / "source.jpg"
    Image.new("RGB", (1200, 800), (20, 20, 20)).save(image_path, format="JPEG")

    settings = AppSettings.default()
    result = apply_date_watermark(image_path, datetime(2025, 4, 13), settings)
    original = Image.open(image_path)

    assert result.size == (1200, 800)
    assert result.tobytes() != original.tobytes()
