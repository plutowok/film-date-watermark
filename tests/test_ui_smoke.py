from datetime import date
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from core.models import AppSettings
from ui.main_window import MainWindow


def test_main_window_instantiates():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() != ""
    assert window.red_packet_button.text()
    assert window.support_author_button.text()


def test_load_settings_populates_all_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.settings = AppSettings.spec_defaults()
    window.settings.opacity = 0.75
    window.settings.font_size_ratio = 0.025
    window.settings.margin_ratio = 0.025
    window.settings.bottom_margin_ratio = 0.04
    window.settings.color_rgb = (210, 80, 20)
    window.settings.second_line_mode = "birthday"
    window.settings.occasion_prefix = "生日"
    window.settings.occasion_date = date(2025, 2, 12)
    window.settings.custom_text = "百天快乐"
    window._load_settings_to_ui()

    assert window.opacity_spin.value() == 75
    assert window.font_ratio_spin.value() == 2.5
    assert window.margin_ratio_spin.value() == 2.5
    assert window.bottom_margin_ratio_spin.value() == 4.0
    assert tuple(window.color_preview.property("rgb")) == (210, 80, 20)
    assert window.second_line_mode_combo.currentData() == "birthday"
    assert window.occasion_prefix_edit.text() == "生日"
    assert window.occasion_date_edit.date().toPython() == date(2025, 2, 12)
    assert window.custom_text_edit.text() == "百天快乐"


def test_preview_navigation_cycles_between_selected_images(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    image_paths = []
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        image_path = tmp_path / name
        Image.new("RGB", (200, 120), (10, 10, 10)).save(image_path, format="JPEG")
        image_paths.append(image_path)

    window.selected_paths = image_paths
    window.preview_index = 0

    window._refresh_preview()
    assert window.preview_index_label.text() == "1 / 3"
    assert window.preview_file_label.text().endswith("a.jpg")

    window._show_next_preview()
    assert window.preview_index_label.text() == "2 / 3"
    assert window.preview_file_label.text().endswith("b.jpg")

    window._show_previous_preview()
    assert window.preview_index_label.text() == "1 / 3"
    assert window.preview_file_label.text().endswith("a.jpg")

    window._show_previous_preview()
    assert window.preview_index_label.text() == "3 / 3"
    assert window.preview_file_label.text().endswith("c.jpg")
