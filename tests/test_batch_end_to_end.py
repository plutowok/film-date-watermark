from pathlib import Path

import piexif
from PIL import Image

from core.batch_processor import process_single_file
from core.models import AppSettings


def test_process_single_file_writes_output_with_report_fields(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    source = root / "photo.jpg"
    exif_bytes = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: b"2025:04:13 10:20:30"}})
    Image.new("RGB", (800, 600), (20, 20, 20)).save(source, format="JPEG", exif=exif_bytes)

    settings = AppSettings.default()
    result = process_single_file(root, source, settings)

    assert result.status == "success"
    assert Path(result.output_path).exists()
    assert result.date_source == "exif"


def test_process_single_file_normalizes_orientation_for_portrait_output(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    source = root / "portrait.jpg"
    exif_bytes = piexif.dump(
        {
            "0th": {piexif.ImageIFD.Orientation: 6},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2025:04:13 10:20:30"},
        }
    )
    Image.new("RGB", (800, 600), (20, 20, 20)).save(source, format="JPEG", exif=exif_bytes)

    settings = AppSettings.default()
    result = process_single_file(root, source, settings)
    output = Image.open(result.output_path)

    assert result.status == "success"
    assert output.height > output.width
