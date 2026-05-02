from core.models import AppSettings, FileProcessResult


def test_spec_default_settings_match_base_style():
    settings = AppSettings.spec_defaults()

    assert settings.date_format == "yy mm dd"
    assert settings.color_rgb == (233, 110, 37)
    assert settings.opacity == 0.75
    assert settings.font_size_ratio == 0.025
    assert settings.margin_ratio == 0.025
    assert settings.bottom_margin_ratio == 0.025
    assert settings.output_dir_name == "dated_output"
    assert settings.failed_dir_name == "dated_failed"
    assert settings.use_file_mtime_fallback is False
    assert settings.second_line_mode == "off"
    assert settings.occasion_prefix == ""
    assert settings.custom_text == ""


def test_runtime_saved_settings_override_bundled_defaults(monkeypatch, tmp_path):
    bundled_root = tmp_path / "bundle"
    bundled_root.mkdir()
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()

    (bundled_root / "default_settings.json").write_text(
        '{"date_format":"yyyy.mm.dd","color_rgb":[200,58,23],"opacity":0.65,"font_size_ratio":0.03,"margin_ratio":0.02,"bottom_margin_ratio":0.02,"font_path":"DS-DIGIB-2.ttf","output_dir_name":"dated_output","failed_dir_name":"dated_failed","use_file_mtime_fallback":false,"use_unified_date":false,"unified_date":null,"second_line_mode":"off","occasion_prefix":"","occasion_date":null,"custom_text":"","prefix":"","suffix":""}',
        encoding="utf-8",
    )
    (runtime_root / "watermark_settings.json").write_text(
        '{"date_format":"yyyy.mm.dd","color_rgb":[233,64,34],"opacity":0.75,"font_size_ratio":0.025,"margin_ratio":0.025,"bottom_margin_ratio":0.04,"font_path":"DS-DIGIB-2.ttf","output_dir_name":"dated_output","failed_dir_name":"dated_failed","use_file_mtime_fallback":false,"use_unified_date":false,"unified_date":null,"second_line_mode":"birthday","occasion_prefix":"生日","occasion_date":"2025-02-12","custom_text":"","prefix":"","suffix":""}',
        encoding="utf-8",
    )

    monkeypatch.setattr("core.models.Path.cwd", lambda: runtime_root)
    monkeypatch.setattr("core.models.sys._MEIPASS", str(bundled_root), raising=False)

    settings = AppSettings.default()

    assert settings.color_rgb == (233, 64, 34)
    assert settings.opacity == 0.75
    assert settings.margin_ratio == 0.025
    assert settings.bottom_margin_ratio == 0.04
    assert settings.second_line_mode == "birthday"
    assert settings.occasion_prefix == "生日"


def test_legacy_anniversary_settings_still_load():
    settings = AppSettings.from_dict(
        {
            "date_format": "yyyy.mm.dd",
            "prefix": "",
            "suffix": "",
            "color_rgb": [233, 110, 37],
            "opacity": 0.75,
            "font_size_ratio": 0.025,
            "margin_ratio": 0.025,
            "bottom_margin_ratio": 0.025,
            "font_path": "DS-DIGIB-2.ttf",
            "output_dir_name": "dated_output",
            "failed_dir_name": "dated_failed",
            "use_file_mtime_fallback": False,
            "use_unified_date": False,
            "unified_date": None,
            "enable_anniversary_mode": True,
            "anniversary_prefix": "纪念",
            "anniversary_date": "2025-02-12",
        }
    )

    assert settings.second_line_mode == "anniversary"
    assert settings.occasion_prefix == "纪念"


def test_result_helpers_capture_success():
    result = FileProcessResult.success(
        source_path="a.jpg",
        output_path="dated_output/a.jpg",
        date_source="exif",
    )

    assert result.status == "success"
    assert result.reason == ""
    assert result.date_source == "exif"
