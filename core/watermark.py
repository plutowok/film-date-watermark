from __future__ import annotations

import sys
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont, ImageOps

from core.models import AppSettings


@dataclass(slots=True)
class WatermarkLayout:
    primary_text: str
    secondary_text: str
    block_width: int
    block_height: int
    primary_width: int
    primary_height: int
    secondary_width: int
    secondary_height: int
    line_gap: int


def resolve_font_path(font_path: str) -> str:
    candidate = Path(font_path)
    if candidate.exists():
        return str(candidate)

    root = Path(__file__).resolve().parent.parent
    if not candidate.is_absolute():
        relative_candidate = root / candidate
        if relative_candidate.exists():
            return str(relative_candidate)

    if getattr(sys, "_MEIPASS", None):
        bundled = Path(sys._MEIPASS) / candidate
        if bundled.exists():
            return str(bundled)
        bundled = Path(sys._MEIPASS) / Path(font_path).name
        if bundled.exists():
            return str(bundled)

    project_font = root / Path(font_path).name
    if project_font.exists():
        return str(project_font)

    raise FileNotFoundError(f"font file not found: {font_path}")


def resolve_chinese_font_path() -> str:
    return resolve_font_path("\u5b57\u4f53\u5e93/ZCOOL_QingKe_HuangYou/ZCOOLQingKeHuangYou-Regular.ttf")


def resolve_songti_font_path() -> str:
    candidates = (
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/simsun.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return resolve_chinese_font_path()


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
    bottom_margin_ratio: float | None = None,
) -> tuple[int, int]:
    margin_x = max(1, int(image_width * margin_ratio))
    margin_y = max(1, int(image_height * (bottom_margin_ratio if bottom_margin_ratio is not None else margin_ratio)))
    draw_x = image_width - margin_x - text_width
    draw_y = image_height - margin_y - text_height
    draw_x = max(margin_x, draw_x)
    draw_y = max(margin_y, draw_y)
    return draw_x, draw_y


def compute_font_pixel_size(image_width: int, image_height: int, font_size_ratio: float) -> int:
    return max(12, int(max(image_width, image_height) * font_size_ratio))


def load_font(font_path: str, image_width: int, image_height: int, font_size_ratio: float) -> ImageFont.FreeTypeFont:
    size = compute_font_pixel_size(image_width, image_height, font_size_ratio)
    return ImageFont.truetype(resolve_font_path(font_path), size=size)


def measure_text(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    temp = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


@lru_cache(maxsize=64)
def load_font_codepoints(font_path: str) -> frozenset[int]:
    resolved_path = resolve_font_path(font_path)
    font_file = Path(resolved_path)
    codepoints: set[int] = set()
    fonts: list[TTFont]

    if font_file.suffix.lower() in {".ttc", ".otc"}:
        collection = TTCollection(resolved_path)
        fonts = list(collection.fonts)
    else:
        fonts = [TTFont(resolved_path)]

    try:
        for font in fonts:
            cmap = font["cmap"]
            for table in cmap.tables:
                if table.isUnicode():
                    codepoints.update(table.cmap.keys())
    finally:
        for font in fonts:
            font.close()

    return frozenset(codepoints)


def font_supports_text(font_path: str, text: str) -> bool:
    required = {ord(character) for character in text if not character.isspace()}
    if not required:
        return True
    try:
        codepoints = load_font_codepoints(font_path)
    except Exception:
        return False
    return required.issubset(codepoints)


def choose_han_font_path(primary_font_path: str, sample_text: str) -> str:
    if font_supports_text(primary_font_path, sample_text):
        return resolve_font_path(primary_font_path)
    return resolve_songti_font_path()


def choose_text_font_path(primary_font_path: str, sample_text: str) -> str:
    if font_supports_text(primary_font_path, sample_text):
        return resolve_font_path(primary_font_path)
    if any("\u4e00" <= character <= "\u9fff" for character in sample_text):
        return resolve_songti_font_path()
    return resolve_font_path(primary_font_path)


def calculate_anniversary_delta(photo_date: date, anchor_date: date) -> tuple[int, int, int]:
    start, end = sorted((photo_date, anchor_date))

    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day

    if days < 0:
        months -= 1
        previous_month = end.month - 1 or 12
        previous_month_year = end.year if end.month > 1 else end.year - 1
        days += monthrange(previous_month_year, previous_month)[1]

    if months < 0:
        years -= 1
        months += 12

    return years, months, days


def build_anniversary_segments(photo_date: date, anniversary_date: date, prefix: str) -> list[tuple[str, str]]:
    years, months, days = calculate_anniversary_delta(photo_date, anniversary_date)
    segments: list[tuple[str, str]] = []
    if prefix:
        segments.append((prefix, "text"))

    if years > 0:
        segments.extend(
            [
                (str(years), "digit"),
                ("\u5e74", "text"),
                (str(months), "digit"),
                ("\u4e2a\u6708", "text"),
                (str(days), "digit"),
                ("\u5929", "text"),
            ]
        )
    elif months > 0:
        segments.extend(
            [
                (str(months), "digit"),
                ("\u4e2a\u6708", "text"),
                (str(days), "digit"),
                ("\u5929", "text"),
            ]
        )
    else:
        segments.extend([(str(days), "digit"), ("\u5929", "text")])

    return segments


def build_birthday_segments(photo_date: date, birthday_date: date, prefix: str) -> list[tuple[str, str]]:
    years, months, days = calculate_anniversary_delta(photo_date, birthday_date)
    segments: list[tuple[str, str]] = []
    if prefix:
        segments.append((prefix, "text"))

    if years > 0:
        segments.extend(
            [
                (str(years), "digit"),
                ("\u5c81", "text"),
                (str(months), "digit"),
                ("\u4e2a\u6708", "text"),
            ]
        )
    elif months > 0:
        segments.extend(
            [
                (str(months), "digit"),
                ("\u4e2a\u6708", "text"),
                (str(days), "digit"),
                ("\u5929", "text"),
            ]
        )
    else:
        segments.extend([(str(days), "digit"), ("\u5929", "text")])

    return segments


def build_secondary_line(
    value: datetime,
    second_line_mode: str,
    occasion_prefix: str,
    occasion_date: date | None,
    custom_text: str,
) -> tuple[str, list[tuple[str, str]]]:
    if second_line_mode == "anniversary" and occasion_date:
        segments = build_anniversary_segments(value.date(), occasion_date, occasion_prefix)
    elif second_line_mode == "birthday" and occasion_date:
        segments = build_birthday_segments(value.date(), occasion_date, occasion_prefix)
    elif second_line_mode == "custom":
        text = custom_text.strip()
        if not text:
            return "", []
        return text, [(text, "text")]
    else:
        return "", []

    return "".join(text for text, _ in segments), segments


def measure_segments(
    segments: list[tuple[str, str]],
    digit_font: ImageFont.FreeTypeFont,
    text_font: ImageFont.FreeTypeFont,
) -> tuple[int, int]:
    widths: list[int] = []
    heights: list[int] = []
    for text, kind in segments:
        font = digit_font if kind == "digit" else text_font
        width, height = measure_text(text, font)
        widths.append(width)
        heights.append(height)
    return sum(widths), max(heights, default=0)


def layout_watermark(image_width: int, image_height: int, value: datetime, settings: AppSettings) -> WatermarkLayout:
    digit_font = load_font(settings.font_path, image_width, image_height, settings.font_size_ratio)
    primary_text = format_date_text(value, settings.date_format, settings.prefix, settings.suffix)
    primary_width, primary_height = measure_text(primary_text, digit_font)

    secondary_text, segments = build_secondary_line(
        value,
        settings.second_line_mode,
        settings.occasion_prefix,
        settings.occasion_date,
        settings.custom_text,
    )
    secondary_width = 0
    secondary_height = 0
    line_gap = 0

    if segments:
        secondary_digit_font = load_font(settings.font_path, image_width, image_height, settings.font_size_ratio * 0.92)
        text_font_path = choose_text_font_path(settings.font_path, secondary_text)
        text_font = ImageFont.truetype(
            text_font_path,
            size=max(11, secondary_digit_font.size - 1),
        )
        secondary_width, secondary_height = measure_segments(segments, secondary_digit_font, text_font)
        line_gap = max(4, int(primary_height * 0.5))

    block_width = max(primary_width, secondary_width)
    block_height = primary_height + (line_gap + secondary_height if secondary_text else 0)

    return WatermarkLayout(
        primary_text=primary_text,
        secondary_text=secondary_text,
        block_width=block_width,
        block_height=block_height,
        primary_width=primary_width,
        primary_height=primary_height,
        secondary_width=secondary_width,
        secondary_height=secondary_height,
        line_gap=line_gap,
    )


def draw_segments(
    draw: ImageDraw.ImageDraw,
    start_x: int,
    baseline_y: int,
    segments: list[tuple[str, str]],
    digit_font: ImageFont.FreeTypeFont,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
) -> None:
    current_x = start_x
    for text, kind in segments:
        font = digit_font if kind == "digit" else text_font
        draw.text((current_x, baseline_y), text, font=font, fill=fill)
        width, _ = measure_text(text, font)
        current_x += width


def apply_date_watermark(image_path: Path, value: datetime, settings: AppSettings) -> Image.Image:
    source_image = ImageOps.exif_transpose(Image.open(image_path)).convert("RGBA")
    overlay = Image.new("RGBA", source_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    digit_font = load_font(settings.font_path, source_image.width, source_image.height, settings.font_size_ratio)
    layout = layout_watermark(source_image.width, source_image.height, value, settings)
    draw_x, draw_y = compute_text_position(
        image_width=source_image.width,
        image_height=source_image.height,
        text_width=layout.block_width,
        text_height=layout.block_height,
        margin_ratio=settings.margin_ratio,
        bottom_margin_ratio=settings.bottom_margin_ratio,
    )
    rgba = (*settings.color_rgb, max(0, min(255, int(settings.opacity * 255))))
    primary_x = draw_x + layout.block_width - layout.primary_width
    draw.text((primary_x, draw_y), layout.primary_text, font=digit_font, fill=rgba)

    secondary_text, segments = build_secondary_line(
        value,
        settings.second_line_mode,
        settings.occasion_prefix,
        settings.occasion_date,
        settings.custom_text,
    )
    if secondary_text and segments:
        secondary_digit_font = load_font(
            settings.font_path,
            source_image.width,
            source_image.height,
            settings.font_size_ratio * 0.92,
        )
        text_font_path = choose_text_font_path(settings.font_path, secondary_text)
        text_font = ImageFont.truetype(
            text_font_path,
            size=max(11, secondary_digit_font.size - 1),
        )
        secondary_x = draw_x + layout.block_width - layout.secondary_width
        secondary_y = draw_y + layout.primary_height + layout.line_gap
        draw_segments(draw, secondary_x, secondary_y, segments, secondary_digit_font, text_font, rgba)

    return Image.alpha_composite(source_image, overlay).convert("RGB")
