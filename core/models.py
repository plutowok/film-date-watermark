from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppSettings:
    date_format: str
    prefix: str
    suffix: str
    color_rgb: tuple[int, int, int]
    opacity: float
    font_size_ratio: float
    margin_ratio: float
    bottom_margin_ratio: float
    font_path: str
    output_dir_name: str
    failed_dir_name: str
    use_file_mtime_fallback: bool
    use_unified_date: bool
    unified_date: date | None
    second_line_mode: str
    occasion_prefix: str
    occasion_date: date | None
    custom_text: str

    @classmethod
    def spec_defaults(cls) -> "AppSettings":
        return cls(
            date_format="yy mm dd",
            prefix="",
            suffix="",
            color_rgb=(233, 110, 37),
            opacity=0.75,
            font_size_ratio=0.025,
            margin_ratio=0.025,
            bottom_margin_ratio=0.025,
            font_path=str(Path(__file__).resolve().parent.parent / "DS-DIGIB-2.ttf"),
            output_dir_name="dated_output",
            failed_dir_name="dated_failed",
            use_file_mtime_fallback=False,
            use_unified_date=False,
            unified_date=None,
            second_line_mode="off",
            occasion_prefix="",
            occasion_date=None,
            custom_text="",
        )

    @classmethod
    def default(cls) -> "AppSettings":
        settings = cls.spec_defaults()

        bundled_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        runtime_root = Path.cwd()
        candidates = (
            bundled_root / "default_settings.json",
            runtime_root / "default_settings.json",
            runtime_root / "watermark_settings.json",
        )

        for candidate in candidates:
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                merged = settings.to_dict()
                merged.update(data)
                settings = cls.from_dict(merged)
        return settings

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["unified_date"] = self.unified_date.isoformat() if self.unified_date else None
        data["occasion_date"] = self.occasion_date.isoformat() if self.occasion_date else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        copied = dict(data)
        if copied.get("unified_date"):
            copied["unified_date"] = date.fromisoformat(copied["unified_date"])
        if copied.get("occasion_date"):
            copied["occasion_date"] = date.fromisoformat(copied["occasion_date"])
        if copied.get("anniversary_date") and not copied.get("occasion_date"):
            copied["occasion_date"] = date.fromisoformat(copied["anniversary_date"])
        if "color_rgb" in copied:
            copied["color_rgb"] = tuple(copied["color_rgb"])
        if "bottom_margin_ratio" not in copied:
            copied["bottom_margin_ratio"] = copied.get("margin_ratio", 0.025)

        if "second_line_mode" not in copied:
            legacy_enabled = copied.get("enable_anniversary_mode", False)
            copied["second_line_mode"] = "anniversary" if legacy_enabled else "off"
        if "occasion_prefix" not in copied:
            copied["occasion_prefix"] = copied.get("anniversary_prefix", "")
        if "occasion_date" not in copied:
            copied["occasion_date"] = None
        if "custom_text" not in copied:
            copied["custom_text"] = ""

        copied.pop("enable_anniversary_mode", None)
        copied.pop("anniversary_prefix", None)
        copied.pop("anniversary_date", None)
        return cls(**copied)


@dataclass(slots=True)
class ResolvedDate:
    value: datetime
    source: str
    source_label: str


@dataclass(slots=True)
class PreviewResult:
    preview_image: Any
    source_label: str
    text: str


@dataclass(slots=True)
class FileProcessResult:
    source_path: str
    status: str
    output_path: str
    date_source: str
    reason: str

    @classmethod
    def success(cls, source_path: str, output_path: str, date_source: str) -> "FileProcessResult":
        return cls(
            source_path=source_path,
            status="success",
            output_path=output_path,
            date_source=date_source,
            reason="",
        )

    @classmethod
    def failed(cls, source_path: str, output_path: str, reason: str) -> "FileProcessResult":
        return cls(
            source_path=source_path,
            status="failed",
            output_path=output_path,
            date_source="",
            reason=reason,
        )
