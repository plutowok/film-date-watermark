from datetime import date, datetime
from pathlib import Path

from core.date_source import resolve_photo_date
from core.models import AppSettings


def test_unified_date_overrides_everything(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test")
    settings = AppSettings.default()
    settings.use_unified_date = True
    settings.unified_date = date(2025, 4, 13)

    resolved = resolve_photo_date(image_path, settings, exif_map={"DateTimeOriginal": "2024:01:01 08:00:00"})

    assert resolved.value == datetime(2025, 4, 13)
    assert resolved.source == "unified"


def test_exif_priority_order(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test")
    settings = AppSettings.default()

    resolved = resolve_photo_date(
        image_path,
        settings,
        exif_map={"DateTimeDigitized": "2025:04:13 10:20:30"},
    )

    assert resolved.value == datetime(2025, 4, 13, 10, 20, 30)
    assert resolved.source == "exif"


def test_missing_exif_raises_without_fallback(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test")
    settings = AppSettings.default()

    try:
        resolve_photo_date(image_path, settings, exif_map={})
    except ValueError as exc:
        assert "EXIF" in str(exc)
    else:
        raise AssertionError("expected ValueError")
