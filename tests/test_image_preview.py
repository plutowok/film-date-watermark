from datetime import date
from pathlib import Path

import piexif
from PIL import Image

from core.image_preview import build_preview
from core.models import AppSettings


def test_build_preview_returns_overlay_and_label(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    exif_bytes = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: b"2025:04:13 10:20:30"}})
    Image.new("RGB", (640, 480), (10, 10, 10)).save(image_path, format="JPEG", exif=exif_bytes)

    settings = AppSettings.spec_defaults()
    preview = build_preview(image_path, settings)

    assert preview.preview_image.size == (640, 480)
    assert preview.source_label.startswith("EXIF:")
    assert preview.text == "25 04 13"


def test_build_preview_uses_birthday_secondary_line(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    exif_bytes = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: b"2026:08:15 10:20:30"}})
    Image.new("RGB", (640, 480), (10, 10, 10)).save(image_path, format="JPEG", exif=exif_bytes)

    settings = AppSettings.spec_defaults()
    settings.second_line_mode = "birthday"
    settings.occasion_prefix = "\u5b9d\u5b9d"
    settings.occasion_date = date(2024, 3, 12)
    preview = build_preview(image_path, settings)

    assert preview.text == "26 08 15\n宝宝2岁5个月"
