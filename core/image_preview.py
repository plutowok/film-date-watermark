from __future__ import annotations

from pathlib import Path

from core.batch_processor import read_exif_map
from core.date_source import resolve_photo_date
from core.models import AppSettings, PreviewResult
from core.watermark import apply_date_watermark, build_secondary_line, format_date_text


def build_preview(image_path: Path, settings: AppSettings) -> PreviewResult:
    exif_map, _ = read_exif_map(image_path)
    resolved = resolve_photo_date(image_path, settings, exif_map)
    preview_image = apply_date_watermark(image_path, resolved.value, settings)
    text = format_date_text(resolved.value, settings.date_format, settings.prefix, settings.suffix)
    secondary_text, _ = build_secondary_line(
        resolved.value,
        settings.second_line_mode,
        settings.occasion_prefix,
        settings.occasion_date,
        settings.custom_text,
    )
    if secondary_text:
        text = f"{text}\n{secondary_text}"
    return PreviewResult(preview_image=preview_image, source_label=resolved.source_label, text=text)
