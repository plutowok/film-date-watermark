from __future__ import annotations

import json
from pathlib import Path

from core.models import AppSettings


def normalize_font_path(font_path: str) -> str:
    root = Path(__file__).resolve().parent.parent
    candidate = Path(font_path)
    if candidate.exists():
        try:
            return candidate.relative_to(root).as_posix()
        except ValueError:
            pass

    basename = candidate.name
    if not basename:
        return font_path

    for matched in root.rglob(basename):
        if matched.is_file():
            return matched.relative_to(root).as_posix()
    return font_path


def save_settings(path: Path, settings: AppSettings) -> None:
    data = settings.to_dict()
    data["font_path"] = normalize_font_path(data["font_path"])
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings(path: Path) -> AppSettings:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AppSettings.from_dict(data)
