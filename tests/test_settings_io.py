from pathlib import Path

from core.models import AppSettings
from core.settings_io import load_settings, save_settings


def test_save_and_load_settings_round_trip(tmp_path: Path):
    path = tmp_path / "watermark_settings.json"
    settings = AppSettings.default()
    settings.prefix = "DATE "
    settings.use_file_mtime_fallback = True
    settings.second_line_mode = "custom"
    settings.custom_text = "宝宝出生第100天"
    settings.font_path = str(
        Path(__file__).resolve().parent.parent / "字体库" / "ZCOOL_QingKe_HuangYou" / "ZCOOLQingKeHuangYou-Regular.ttf"
    )

    save_settings(path, settings)
    loaded = load_settings(path)

    assert loaded.prefix == "DATE "
    assert loaded.use_file_mtime_fallback is True
    assert loaded.output_dir_name == "dated_output"
    assert loaded.second_line_mode == "custom"
    assert loaded.custom_text == "宝宝出生第100天"
    assert loaded.font_path == "字体库/ZCOOL_QingKe_HuangYou/ZCOOLQingKeHuangYou-Regular.ttf"
