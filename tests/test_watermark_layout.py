from datetime import datetime
from pathlib import Path

from core.watermark import (
    build_anniversary_segments,
    build_birthday_segments,
    build_secondary_line,
    choose_han_font_path,
    compute_font_pixel_size,
    compute_text_position,
    format_date_text,
)


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
        bottom_margin_ratio=0.011,
    )

    assert x >= 11
    assert y >= 6
    assert x + 180 <= 989
    assert y + 40 <= 594


def test_bottom_margin_ratio_uses_vertical_override():
    _, y = compute_text_position(
        image_width=1000,
        image_height=600,
        text_width=180,
        text_height=40,
        margin_ratio=0.011,
        bottom_margin_ratio=0.05,
    )

    assert y + 40 <= 570


def test_same_long_edge_uses_same_font_size():
    landscape_size = compute_font_pixel_size(1200, 800, 0.025)
    portrait_size = compute_font_pixel_size(800, 1200, 0.025)

    assert landscape_size == portrait_size


def test_anniversary_segments_keep_zero_tail_units():
    segments = build_anniversary_segments(datetime(2026, 1, 10).date(), datetime(2025, 2, 12).date(), "\u7eaa\u5ff5")
    assert "".join(text for text, _ in segments) == "\u7eaa\u5ff510\u4e2a\u670829\u5929"


def test_anniversary_segments_start_from_days_when_needed():
    segments = build_anniversary_segments(datetime(2025, 2, 13).date(), datetime(2025, 2, 12).date(), "")
    assert "".join(text for text, _ in segments) == "1\u5929"


def test_anniversary_segments_use_calendar_borrowing():
    segments = build_anniversary_segments(datetime(2026, 1, 31).date(), datetime(2025, 7, 31).date(), "")
    assert "".join(text for text, _ in segments) == "6\u4e2a\u67080\u5929"


def test_birthday_segments_hide_days_after_one_year():
    segments = build_birthday_segments(datetime(2026, 8, 15).date(), datetime(2024, 3, 12).date(), "\u5b9d\u5b9d")
    assert "".join(text for text, _ in segments) == "\u5b9d\u5b9d2\u5c815\u4e2a\u6708"


def test_birthday_segments_show_months_and_days_under_one_year():
    segments = build_birthday_segments(datetime(2025, 8, 15).date(), datetime(2025, 3, 12).date(), "")
    assert "".join(text for text, _ in segments) == "5\u4e2a\u67083\u5929"


def test_build_secondary_line_returns_custom_text():
    text, segments = build_secondary_line(
        datetime(2025, 4, 13),
        "custom",
        "",
        None,
        "\u81ea\u5b9a\u4e49\u6587\u6848",
    )

    assert text == "\u81ea\u5b9a\u4e49\u6587\u6848"
    assert segments == [("\u81ea\u5b9a\u4e49\u6587\u6848", "text")]


def test_choose_han_font_path_uses_selected_font_when_it_contains_chinese():
    font_path = Path("H:/\u4ee3\u7801/\u80f6\u7247\u65e5\u671f\u6c34\u5370/\u5b57\u4f53\u5e93/ZCOOL_QingKe_HuangYou/ZCOOLQingKeHuangYou-Regular.ttf")

    assert choose_han_font_path(str(font_path), "\u5e74\u6708\u5929") == str(font_path)


def test_choose_han_font_path_falls_back_when_selected_font_lacks_chinese():
    font_path = Path(
        "H:/\u4ee3\u7801/\u80f6\u7247\u65e5\u671f\u6c34\u5370/\u5b57\u4f53\u5e93/Bitcount_Grid_Single/static/BitcountGridSingle-Regular.ttf"
    )

    assert choose_han_font_path(str(font_path), "\u5e74\u6708\u5929") != str(font_path)
