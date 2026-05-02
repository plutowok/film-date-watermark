from __future__ import annotations

import csv
import os
import shutil
from os import utime
from pathlib import Path

import piexif
from PIL import Image

from core.date_source import resolve_photo_date
from core.models import AppSettings, FileProcessResult
from core.watermark import apply_date_watermark

JPEG_EXTENSIONS = {".jpg", ".jpeg"}


def collect_jpegs(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in JPEG_EXTENSIONS
    )


def determine_root(paths: list[Path]) -> Path:
    if not paths:
        raise ValueError("未选择任何图片")
    if len(paths) == 1:
        return paths[0].parent
    common = os.path.commonpath([str(path.parent) for path in paths])
    return Path(common)


def ensure_output_path(root: Path, source: Path, folder_name: str) -> Path:
    relative = source.relative_to(root)
    target = root / folder_name / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def write_report(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "status", "date_source", "reason", "output_path"],
        )
        writer.writeheader()
        writer.writerows(rows)


def read_exif_map(source: Path) -> tuple[dict[str, str], bytes]:
    image = Image.open(source)
    exif_bytes = image.info.get("exif", b"")
    if not exif_bytes:
        return {}, b""

    exif_dict = piexif.load(exif_bytes)
    result: dict[str, str] = {}

    exif_mapping = {
        "DateTimeOriginal": piexif.ExifIFD.DateTimeOriginal,
        "DateTimeDigitized": piexif.ExifIFD.DateTimeDigitized,
    }
    for key, exif_key in exif_mapping.items():
        value = exif_dict.get("Exif", {}).get(exif_key)
        if value:
            result[key] = value.decode("utf-8", errors="ignore")

    image_datetime = exif_dict.get("0th", {}).get(piexif.ImageIFD.DateTime)
    if image_datetime:
        result["DateTime"] = image_datetime.decode("utf-8", errors="ignore")

    return result, exif_bytes


def normalize_exif_bytes(exif_bytes: bytes) -> bytes:
    if not exif_bytes:
        return b""
    exif_dict = piexif.load(exif_bytes)
    exif_dict.setdefault("0th", {})[piexif.ImageIFD.Orientation] = 1
    return piexif.dump(exif_dict)


def process_single_file(root: Path, source: Path, settings: AppSettings) -> FileProcessResult:
    failed_target = ensure_output_path(root, source, settings.failed_dir_name)
    try:
        exif_map, exif_bytes = read_exif_map(source)
        resolved = resolve_photo_date(source, settings, exif_map)
        target = ensure_output_path(root, source, settings.output_dir_name)
        rendered = apply_date_watermark(source, resolved.value, settings)
        save_kwargs: dict[str, object] = {"format": "JPEG", "quality": 95}
        normalized_exif = normalize_exif_bytes(exif_bytes)
        if normalized_exif:
            save_kwargs["exif"] = normalized_exif
        rendered.save(target, **save_kwargs)
        source_stat = source.stat()
        utime(target, (source_stat.st_atime, source_stat.st_mtime))
        return FileProcessResult.success(str(source), str(target), resolved.source)
    except Exception as exc:
        shutil.copy2(source, failed_target)
        return FileProcessResult.failed(str(source), str(failed_target), str(exc))


def process_files(root: Path, files: list[Path], settings: AppSettings) -> tuple[list[FileProcessResult], Path]:
    results: list[FileProcessResult] = []
    report_rows: list[dict[str, str]] = []

    for file_path in files:
        result = process_single_file(root, file_path, settings)
        results.append(result)
        report_rows.append(
            {
                "source_path": result.source_path,
                "status": result.status,
                "date_source": result.date_source,
                "reason": result.reason,
                "output_path": result.output_path,
            }
        )

    report_path = root / settings.output_dir_name / "process_report.csv"
    write_report(report_path, report_rows)
    return results, report_path
