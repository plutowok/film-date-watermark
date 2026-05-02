from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.models import AppSettings, ResolvedDate


EXIF_DATE_KEYS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def parse_exif_datetime(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")


def resolve_photo_date(path: Path, settings: AppSettings, exif_map: dict[str, str]) -> ResolvedDate:
    if settings.use_unified_date and settings.unified_date is not None:
        value = datetime.combine(settings.unified_date, datetime.min.time())
        return ResolvedDate(
            value=value,
            source="unified",
            source_label=f"统一日期: {settings.unified_date.isoformat()}",
        )

    for key in EXIF_DATE_KEYS:
        raw_value = exif_map.get(key)
        if raw_value:
            value = parse_exif_datetime(raw_value)
            return ResolvedDate(value=value, source="exif", source_label=f"EXIF: {raw_value}")

    if settings.use_file_mtime_fallback:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return ResolvedDate(
            value=mtime,
            source="mtime_fallback",
            source_label=f"文件修改日期回退: {mtime.strftime('%Y-%m-%d %H:%M:%S')}",
        )

    raise ValueError("EXIF 日期缺失")
