# Film Date Watermark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 Python + PySide6 的 Windows 桌面工具，支持批量为 JPG/JPEG 添加胶片日期戳风格水印，并提供预览、设置保存/加载、失败分流和单文件 exe 打包能力。

**Architecture:** 项目拆分为 UI 层和核心处理层。UI 层负责文件选择、参数编辑、预览和批处理触发；核心层负责配置模型、日期来源解析、水印绘制、批量处理、结果日志和设置持久化。核心逻辑优先通过 pytest 覆盖，桌面界面保持薄层调用。

**Tech Stack:** Python 3.11+, PySide6, Pillow, piexif, pytest, PyInstaller

---

### Task 1: 初始化项目骨架与依赖清单

**Files:**
- Create: `H:/代码/胶片日期水印/requirements.txt`
- Create: `H:/代码/胶片日期水印/app.py`
- Create: `H:/代码/胶片日期水印/core/__init__.py`
- Create: `H:/代码/胶片日期水印/ui/__init__.py`
- Create: `H:/代码/胶片日期水印/tests/__init__.py`

- [ ] **Step 1: 写一个最小失败测试，验证入口模块可被导入**

```python
# H:/代码/胶片日期水印/tests/test_app_import.py
import importlib


def test_app_module_importable():
    module = importlib.import_module("app")
    assert module is not None
```

- [ ] **Step 2: 运行测试，确认它先失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_app_import.py -v`
Expected: FAIL，提示 `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: 写最小实现，让测试通过**

```python
# H:/代码/胶片日期水印/app.py
def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```text
# H:/代码/胶片日期水印/requirements.txt
PySide6>=6.8
Pillow>=11.0
piexif>=1.1.3
pytest>=8.0
pyinstaller>=6.0
```

- [ ] **Step 4: 再次运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_app_import.py -v`
Expected: PASS

- [ ] **Step 5: 提交这一小步**

```bash
git add requirements.txt app.py core/__init__.py ui/__init__.py tests/__init__.py tests/test_app_import.py
git commit -m "chore: bootstrap project skeleton"
```

### Task 2: 建立配置模型与处理结果模型

**Files:**
- Create: `H:/代码/胶片日期水印/core/models.py`
- Create: `H:/代码/胶片日期水印/tests/test_models.py`

- [ ] **Step 1: 先写失败测试，锁定默认配置和值对象行为**

```python
# H:/代码/胶片日期水印/tests/test_models.py
from core.models import AppSettings, FileProcessResult


def test_default_settings_match_spec():
    settings = AppSettings.default()

    assert settings.date_format == "yy mm dd"
    assert settings.color_rgb == (233, 110, 37)
    assert settings.opacity == 0.75
    assert settings.font_size_ratio == 0.025
    assert settings.margin_ratio == 0.011
    assert settings.output_dir_name == "dated_output"
    assert settings.failed_dir_name == "dated_failed"
    assert settings.use_file_mtime_fallback is False


def test_result_helpers_capture_success():
    result = FileProcessResult.success(
        source_path="a.jpg",
        output_path="dated_output/a.jpg",
        date_source="exif",
    )

    assert result.status == "success"
    assert result.reason == ""
    assert result.date_source == "exif"
```

- [ ] **Step 2: 运行测试，确认因模型不存在而失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_models.py -v`
Expected: FAIL，提示 `No module named 'core.models'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class AppSettings:
    date_format: str
    prefix: str
    suffix: str
    color_rgb: tuple[int, int, int]
    opacity: float
    font_size_ratio: float
    margin_ratio: float
    font_path: str
    output_dir_name: str
    failed_dir_name: str
    use_file_mtime_fallback: bool
    use_unified_date: bool
    unified_date: date | None

    @classmethod
    def default(cls) -> "AppSettings":
        return cls(
            date_format="yy mm dd",
            prefix="",
            suffix="",
            color_rgb=(233, 110, 37),
            opacity=0.75,
            font_size_ratio=0.025,
            margin_ratio=0.011,
            font_path="DS-DIGIB-2.ttf",
            output_dir_name="dated_output",
            failed_dir_name="dated_failed",
            use_file_mtime_fallback=False,
            use_unified_date=False,
            unified_date=None,
        )


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
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/models.py tests/test_models.py
git commit -m "feat: add settings and result models"
```

### Task 3: 实现日期来源解析

**Files:**
- Create: `H:/代码/胶片日期水印/core/date_source.py`
- Create: `H:/代码/胶片日期水印/tests/test_date_source.py`

- [ ] **Step 1: 写失败测试，覆盖统一日期、EXIF 优先级和 mtime 回退**

```python
# H:/代码/胶片日期水印/tests/test_date_source.py
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

    assert resolved.text_date == datetime(2025, 4, 13)
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

    assert resolved.text_date == datetime(2025, 4, 13, 10, 20, 30)
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
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_date_source.py -v`
Expected: FAIL，提示 `No module named 'core.date_source'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/date_source.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from core.models import AppSettings


@dataclass(slots=True)
class ResolvedDate:
    text_date: datetime
    source: str
    source_label: str


def _parse_exif_datetime(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")


def resolve_photo_date(path: Path, settings: AppSettings, exif_map: dict[str, str]) -> ResolvedDate:
    if settings.use_unified_date and settings.unified_date:
        value = datetime.combine(settings.unified_date, datetime.min.time())
        return ResolvedDate(value, "unified", f"统一日期: {settings.unified_date.isoformat()}")

    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
        raw = exif_map.get(key)
        if raw:
            parsed = _parse_exif_datetime(raw)
            return ResolvedDate(parsed, "exif", f"EXIF: {raw}")

    if settings.use_file_mtime_fallback:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return ResolvedDate(mtime, "mtime_fallback", f"文件修改日期回退: {mtime.isoformat(sep=' ')}")

    raise ValueError("EXIF 日期缺失")
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_date_source.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/date_source.py tests/test_date_source.py
git commit -m "feat: add date source resolution"
```

### Task 4: 实现日期格式化与定位算法

**Files:**
- Create: `H:/代码/胶片日期水印/core/watermark.py`
- Create: `H:/代码/胶片日期水印/tests/test_watermark_layout.py`

- [ ] **Step 1: 先写失败测试，覆盖格式化与不越界定位**

```python
# H:/代码/胶片日期水印/tests/test_watermark_layout.py
from datetime import datetime

from core.watermark import compute_text_position, format_date_text


def test_default_date_format():
    text = format_date_text(datetime(2025, 4, 13), "yy mm dd", prefix="", suffix="")
    assert text == "25 04 13"


def test_dotted_date_format_with_affixes():
    text = format_date_text(datetime(2025, 4, 13), "yyyy.mm.dd", prefix="DATE ", suffix=" OK")
    assert text == "DATE 2025.04.13 OK"


def test_text_position_stays_inside_bounds():
    x, y = compute_text_position(
        image_width=1000,
        image_height=600,
        text_width=180,
        text_height=40,
        margin_ratio=0.011,
    )

    assert x >= 11
    assert y >= 6
    assert x + 180 <= 989
    assert y + 40 <= 594
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_watermark_layout.py -v`
Expected: FAIL，提示 `cannot import name`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/watermark.py
from __future__ import annotations

from datetime import datetime


def format_date_text(value: datetime, date_format: str, prefix: str, suffix: str) -> str:
    if date_format == "yyyy.mm.dd":
        base = value.strftime("%Y.%m.%d")
    else:
        base = value.strftime("%y %m %d")
    return f"{prefix}{base}{suffix}"


def compute_text_position(
    image_width: int,
    image_height: int,
    text_width: int,
    text_height: int,
    margin_ratio: float,
) -> tuple[int, int]:
    x = int(image_width * 0.9)
    y = int(image_height * 0.9)
    margin_x = int(image_width * margin_ratio)
    margin_y = int(image_height * margin_ratio)

    draw_x = x
    draw_y = y

    if draw_x + text_width > image_width - margin_x:
        draw_x = image_width - margin_x - text_width
    if draw_y + text_height > image_height - margin_y:
        draw_y = image_height - margin_y - text_height

    draw_x = max(margin_x, draw_x)
    draw_y = max(margin_y, draw_y)
    return draw_x, draw_y
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_watermark_layout.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/watermark.py tests/test_watermark_layout.py
git commit -m "feat: add date formatting and layout logic"
```

### Task 5: 实现字体加载、文字测量与实际水印绘制

**Files:**
- Modify: `H:/代码/胶片日期水印/core/watermark.py`
- Create: `H:/代码/胶片日期水印/tests/test_watermark_render.py`

- [ ] **Step 1: 先写失败测试，验证水印绘制会改变图像**

```python
# H:/代码/胶片日期水印/tests/test_watermark_render.py
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

    assert result.size == (1200, 800)
    assert list(result.getdata()) != list(Image.open(image_path).getdata())
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_watermark_render.py -v`
Expected: FAIL，提示 `cannot import name 'apply_date_watermark'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/watermark.py
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_font(font_path: str, image_width: int, font_size_ratio: float) -> ImageFont.FreeTypeFont:
    font_size = max(12, int(image_width * font_size_ratio))
    return ImageFont.truetype(font_path, font_size)


def apply_date_watermark(image_path: Path, value: datetime, settings) -> Image.Image:
    image = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    text = format_date_text(value, settings.date_format, settings.prefix, settings.suffix)
    font = load_font(settings.font_path, image.width, settings.font_size_ratio)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x, y = compute_text_position(image.width, image.height, text_width, text_height, settings.margin_ratio)
    rgba = (*settings.color_rgb, int(settings.opacity * 255))
    draw.text((x, y), text, font=font, fill=rgba)
    return Image.alpha_composite(image, overlay).convert("RGB")
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_watermark_render.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/watermark.py tests/test_watermark_render.py
git commit -m "feat: render watermark onto images"
```

### Task 6: 实现设置保存与加载

**Files:**
- Create: `H:/代码/胶片日期水印/core/settings_io.py`
- Create: `H:/代码/胶片日期水印/tests/test_settings_io.py`

- [ ] **Step 1: 写失败测试，验证设置 JSON 往返**

```python
# H:/代码/胶片日期水印/tests/test_settings_io.py
from pathlib import Path

from core.models import AppSettings
from core.settings_io import load_settings, save_settings


def test_save_and_load_settings_round_trip(tmp_path: Path):
    path = tmp_path / "watermark_settings.json"
    settings = AppSettings.default()
    settings.prefix = "DATE "
    settings.use_file_mtime_fallback = True

    save_settings(path, settings)
    loaded = load_settings(path)

    assert loaded.prefix == "DATE "
    assert loaded.use_file_mtime_fallback is True
    assert loaded.output_dir_name == "dated_output"
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_settings_io.py -v`
Expected: FAIL，提示 `No module named 'core.settings_io'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/settings_io.py
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from core.models import AppSettings


def save_settings(path: Path, settings: AppSettings) -> None:
    data = asdict(settings)
    data["unified_date"] = settings.unified_date.isoformat() if settings.unified_date else None
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings(path: Path) -> AppSettings:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["unified_date"]:
        data["unified_date"] = date.fromisoformat(data["unified_date"])
    return AppSettings(**data)
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_settings_io.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/settings_io.py tests/test_settings_io.py
git commit -m "feat: persist app settings as json"
```

### Task 7: 实现批量扫描、输出分流和 CSV 报告

**Files:**
- Create: `H:/代码/胶片日期水印/core/batch_processor.py`
- Create: `H:/代码/胶片日期水印/tests/test_batch_processor.py`

- [ ] **Step 1: 先写失败测试，覆盖目录扫描和成功/失败分流**

```python
# H:/代码/胶片日期水印/tests/test_batch_processor.py
from pathlib import Path

from PIL import Image

from core.batch_processor import collect_jpegs, ensure_output_path


def test_collect_jpegs_recurses(tmp_path: Path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    Image.new("RGB", (10, 10), (1, 2, 3)).save(nested / "photo.jpg", format="JPEG")

    paths = collect_jpegs(tmp_path)

    assert [path.name for path in paths] == ["photo.jpg"]


def test_output_path_preserves_relative_structure(tmp_path: Path):
    root = tmp_path / "root"
    source = root / "x" / "y" / "photo.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"demo")

    target = ensure_output_path(root, source, "dated_output")

    assert target == root / "dated_output" / "x" / "y" / "photo.jpg"
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_batch_processor.py -v`
Expected: FAIL，提示 `No module named 'core.batch_processor'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/batch_processor.py
from __future__ import annotations

import csv
from pathlib import Path


def collect_jpegs(root: Path) -> list[Path]:
    files = [path for path in root.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg"}]
    return sorted(files)


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
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_batch_processor.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/batch_processor.py tests/test_batch_processor.py
git commit -m "feat: add batch scan and output path helpers"
```

### Task 8: 把核心处理串起来，支持保留 EXIF 和文件时间

**Files:**
- Modify: `H:/代码/胶片日期水印/core/batch_processor.py`
- Modify: `H:/代码/胶片日期水印/core/date_source.py`
- Modify: `H:/代码/胶片日期水印/core/watermark.py`
- Create: `H:/代码/胶片日期水印/tests/test_batch_end_to_end.py`

- [ ] **Step 1: 先写失败测试，验证单张图像完整处理**

```python
# H:/代码/胶片日期水印/tests/test_batch_end_to_end.py
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
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_batch_end_to_end.py -v`
Expected: FAIL，提示 `cannot import name 'process_single_file'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/batch_processor.py
import shutil
from os import utime

import piexif
from PIL import Image

from core.date_source import resolve_photo_date
from core.models import FileProcessResult
from core.watermark import apply_date_watermark


def read_exif_map(source: Path) -> tuple[dict[str, str], bytes]:
    image = Image.open(source)
    exif_bytes = image.info.get("exif", b"")
    if not exif_bytes:
        return {}, b""
    exif_dict = piexif.load(exif_bytes)
    result: dict[str, str] = {}
    mapping = {
        "DateTimeOriginal": piexif.ExifIFD.DateTimeOriginal,
        "DateTimeDigitized": piexif.ExifIFD.DateTimeDigitized,
    }
    for key, exif_key in mapping.items():
        raw = exif_dict.get("Exif", {}).get(exif_key)
        if raw:
            result[key] = raw.decode("utf-8")
    raw_0th = exif_dict.get("0th", {}).get(piexif.ImageIFD.DateTime)
    if raw_0th:
        result["DateTime"] = raw_0th.decode("utf-8")
    return result, exif_bytes


def process_single_file(root: Path, source: Path, settings) -> FileProcessResult:
    try:
        exif_map, exif_bytes = read_exif_map(source)
        resolved = resolve_photo_date(source, settings, exif_map)
        target = ensure_output_path(root, source, settings.output_dir_name)
        rendered = apply_date_watermark(source, resolved.text_date, settings)
        rendered.save(target, format="JPEG", quality=95, exif=exif_bytes)
        stat = source.stat()
        utime(target, (stat.st_atime, stat.st_mtime))
        return FileProcessResult.success(str(source), str(target), resolved.source)
    except Exception as exc:
        failed_target = ensure_output_path(root, source, settings.failed_dir_name)
        shutil.copy2(source, failed_target)
        return FileProcessResult(
            source_path=str(source),
            status="failed",
            output_path=str(failed_target),
            date_source="",
            reason=str(exc),
        )
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_batch_end_to_end.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/batch_processor.py core/date_source.py core/watermark.py tests/test_batch_end_to_end.py
git commit -m "feat: process images end to end"
```

### Task 9: 实现预览生成逻辑

**Files:**
- Create: `H:/代码/胶片日期水印/core/image_preview.py`
- Create: `H:/代码/胶片日期水印/tests/test_image_preview.py`

- [ ] **Step 1: 写失败测试，验证预览包含来源标签和图像对象**

```python
# H:/代码/胶片日期水印/tests/test_image_preview.py
from pathlib import Path

import piexif
from PIL import Image

from core.image_preview import build_preview
from core.models import AppSettings


def test_build_preview_returns_overlay_and_label(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    exif_bytes = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: b"2025:04:13 10:20:30"}})
    Image.new("RGB", (640, 480), (10, 10, 10)).save(image_path, format="JPEG", exif=exif_bytes)

    preview = build_preview(image_path, AppSettings.default())

    assert preview.preview_image.size == (640, 480)
    assert preview.source_label.startswith("EXIF:")
    assert preview.text == "25 04 13"
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_image_preview.py -v`
Expected: FAIL，提示 `No module named 'core.image_preview'`

- [ ] **Step 3: 写最小实现**

```python
# H:/代码/胶片日期水印/core/image_preview.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.batch_processor import read_exif_map
from core.date_source import resolve_photo_date
from core.watermark import apply_date_watermark, format_date_text


@dataclass(slots=True)
class PreviewResult:
    preview_image: object
    source_label: str
    text: str


def build_preview(image_path: Path, settings) -> PreviewResult:
    exif_map, _ = read_exif_map(image_path)
    resolved = resolve_photo_date(image_path, settings, exif_map)
    preview_image = apply_date_watermark(image_path, resolved.text_date, settings)
    text = format_date_text(resolved.text_date, settings.date_format, settings.prefix, settings.suffix)
    return PreviewResult(preview_image=preview_image, source_label=resolved.source_label, text=text)
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_image_preview.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add core/image_preview.py tests/test_image_preview.py
git commit -m "feat: add preview generation"
```

### Task 10: 实现主窗口与交互

**Files:**
- Create: `H:/代码/胶片日期水印/ui/main_window.py`
- Modify: `H:/代码/胶片日期水印/app.py`
- Create: `H:/代码/胶片日期水印/tests/test_ui_smoke.py`

- [ ] **Step 1: 写失败测试，验证主窗口可实例化**

```python
# H:/代码/胶片日期水印/tests/test_ui_smoke.py
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def test_main_window_instantiates():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() != ""
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_ui_smoke.py -v`
Expected: FAIL，提示 `No module named 'ui.main_window'`

- [ ] **Step 3: 写最小实现，先搭出界面骨架**

```python
# H:/代码/胶片日期水印/ui/main_window.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import AppSettings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.default()
        self.selected_paths: list[str] = []
        self.setWindowTitle("胶片日期水印")
        self.resize(1280, 820)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(self)
        main_layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        self.select_files_button = QPushButton("选择多个文件")
        self.select_folder_button = QPushButton("选择文件夹")
        self.save_settings_button = QPushButton("保存设置")
        self.load_settings_button = QPushButton("加载设置")
        self.process_button = QPushButton("开始处理")
        toolbar.addWidget(self.select_files_button)
        toolbar.addWidget(self.select_folder_button)
        toolbar.addWidget(self.save_settings_button)
        toolbar.addWidget(self.load_settings_button)
        toolbar.addWidget(self.process_button)
        main_layout.addLayout(toolbar)

        body = QHBoxLayout()
        self.settings_panel = QLabel("设置区")
        self.preview_panel = QLabel("预览区")
        body.addWidget(self.settings_panel, 1)
        body.addWidget(self.preview_panel, 2)
        main_layout.addLayout(body)

        self.setCentralWidget(root)
```

```python
# H:/代码/胶片日期水印/app.py
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_ui_smoke.py -v`
Expected: PASS

- [ ] **Step 5: 继续把交互补全并手工验证**

需要补全以下具体点：

```text
1. 文件多选对话框与文件夹选择对话框
2. 设置区控件：日期格式、统一日期、前后缀、颜色、透明度、字体路径、字体比例、安全边距比例
3. 预览区显示原图与水印图
4. 勾选 mtime 回退时弹窗提醒
5. 处理完成后弹出摘要
6. 保存设置 / 加载设置按钮接入 core.settings_io
7. 开始处理按钮接入 core.batch_processor
```

Manual check:
`python H:/代码/胶片日期水印/app.py`

Expected:
- 能打开窗口
- 能点选文件
- 修改设置后预览刷新
- 能开始处理并生成输出目录

- [ ] **Step 6: 提交**

```bash
git add app.py ui/main_window.py tests/test_ui_smoke.py
git commit -m "feat: build main desktop window"
```

### Task 11: 增加打包脚本与运行说明

**Files:**
- Create: `H:/代码/胶片日期水印/build.ps1`
- Create: `H:/代码/胶片日期水印/README.md`
- Create: `H:/代码/胶片日期水印/tests/test_packaging_files.py`

- [ ] **Step 1: 先写失败测试，验证打包脚本文件存在**

```python
# H:/代码/胶片日期水印/tests/test_packaging_files.py
from pathlib import Path


def test_packaging_files_exist():
    assert Path("H:/代码/胶片日期水印/build.ps1").exists()
    assert Path("H:/代码/胶片日期水印/README.md").exists()
```

- [ ] **Step 2: 跑测试，确认失败**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_packaging_files.py -v`
Expected: FAIL，提示缺少文件

- [ ] **Step 3: 写最小实现**

```powershell
# H:/代码/胶片日期水印/build.ps1
python -m PyInstaller `
  --noconfirm `
  --onefile `
  --windowed `
  --add-data "DS-DIGIB-2.ttf;." `
  app.py
```

```markdown
# 胶片日期水印

## 开发运行

```bash
python -m pip install -r requirements.txt
python app.py
```

## 打包

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m pytest H:/代码/胶片日期水印/tests/test_packaging_files.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add build.ps1 README.md tests/test_packaging_files.py
git commit -m "docs: add packaging instructions"
```

### Task 12: 全量验证

**Files:**
- Modify: `H:/代码/胶片日期水印/` 内所有必要文件

- [ ] **Step 1: 运行核心测试集**

Run: `python -m pytest H:/代码/胶片日期水印/tests -v`
Expected: 所有测试 PASS

- [ ] **Step 2: 手工验证以下场景**

```text
1. 选择多个 JPEG 文件，预览第一张并批量输出到 dated_output
2. 选择文件夹，递归扫描子目录并保留目录结构
3. 缺少 EXIF 且未启用回退时，文件进入 dated_failed
4. 缺少 EXIF 且启用回退时，弹窗提醒后使用文件修改日期
5. 保存设置后再加载，界面值恢复一致
6. 预览图与最终输出图的日期文本位置一致
```

- [ ] **Step 3: 打包验证**

Run: `powershell -ExecutionPolicy Bypass -File H:/代码/胶片日期水印/build.ps1`
Expected: 生成 `dist/app.exe` 或配置后的 exe 文件

- [ ] **Step 4: 最终提交**

```bash
git add .
git commit -m "feat: deliver film date watermark desktop app"
```
