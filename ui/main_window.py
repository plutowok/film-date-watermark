from __future__ import annotations

import base64
import os
from datetime import date
from pathlib import Path

from PIL.ImageQt import ImageQt
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.batch_processor import collect_jpegs, determine_root, process_files
from core.image_preview import build_preview
from core.models import AppSettings
from core.settings_io import load_settings, save_settings
from ui import embedded_assets


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.default()
        self.selected_paths: list[Path] = []
        self.selection_root: Path | None = None
        self.preview_index = 0
        self._is_loading_settings = False
        self._build_ui()
        self._load_settings_to_ui()
        self.setWindowTitle("\u80f6\u7247\u65e5\u671f\u6c34\u5370")
        self.resize(1120, 860)

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self.select_files_button = QPushButton("\u9009\u62e9\u591a\u4e2a\u6587\u4ef6")
        self.select_folder_button = QPushButton("\u9009\u62e9\u6587\u4ef6\u5939")
        self.process_button = QPushButton("\u5f00\u59cb\u5904\u7406")
        self.open_output_button = QPushButton("\u6253\u5f00\u8f93\u51fa\u76ee\u5f55")
        self.save_settings_button = QPushButton("\u4fdd\u5b58\u8bbe\u7f6e")
        self.load_settings_button = QPushButton("\u52a0\u8f7d\u8bbe\u7f6e")
        self.status_label = QLabel("\u672a\u9009\u62e9\u56fe\u7247")
        self.preview_file_label = QLabel("\u9884\u89c8\u6587\u4ef6\uff1a\u65e0")
        for widget in (
            self.select_files_button,
            self.select_folder_button,
            self.process_button,
            self.open_output_button,
            self.save_settings_button,
            self.load_settings_button,
        ):
            toolbar.addWidget(widget)
        toolbar.addStretch(1)
        toolbar.addWidget(self.status_label)
        toolbar.addWidget(self.preview_file_label)
        root_layout.addLayout(toolbar)

        body = QHBoxLayout()
        root_layout.addLayout(body, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body.addWidget(scroll, 1)

        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        scroll.setWidget(settings_container)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        body.addWidget(preview_container, 2)

        source_group = QGroupBox("\u65e5\u671f\u6765\u6e90")
        source_form = QFormLayout(source_group)
        self.date_source_combo = QComboBox()
        self.date_source_combo.addItems(["EXIF", "\u7edf\u4e00\u6307\u5b9a\u65e5\u671f"])
        self.unified_date_edit = QDateEdit()
        self.unified_date_edit.setCalendarPopup(True)
        self.unified_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.fallback_checkbox = QCheckBox("\u7f3a\u5c11 EXIF \u65f6\u6539\u7528\u6587\u4ef6\u4fee\u6539\u65e5\u671f")
        source_form.addRow("\u65e5\u671f\u6765\u6e90", self.date_source_combo)
        source_form.addRow("\u7edf\u4e00\u65e5\u671f", self.unified_date_edit)
        source_form.addRow("", self.fallback_checkbox)

        style_group = QGroupBox("\u6c34\u5370\u6837\u5f0f")
        style_form = QFormLayout(style_group)
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["yy mm dd", "yyyy.mm.dd"])
        self.prefix_edit = QLineEdit()
        self.suffix_edit = QLineEdit()
        self.font_path_edit = QLineEdit()
        self.font_path_button = QPushButton("\u9009\u62e9\u5b57\u4f53")
        font_row = QWidget()
        font_layout = QHBoxLayout(font_row)
        font_layout.setContentsMargins(0, 0, 0, 0)
        font_layout.addWidget(self.font_path_edit, 1)
        font_layout.addWidget(self.font_path_button)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(64, 24)
        self.color_button = QPushButton("\u9009\u62e9\u989c\u8272")
        color_row = QWidget()
        color_layout = QHBoxLayout(color_row)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button)
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(1, 100)
        self.opacity_spin.setSuffix("%")
        self.font_ratio_spin = QDoubleSpinBox()
        self.font_ratio_spin.setRange(0.1, 20.0)
        self.font_ratio_spin.setSingleStep(0.1)
        self.font_ratio_spin.setDecimals(2)
        self.font_ratio_spin.setSuffix("%")
        self.margin_ratio_spin = QDoubleSpinBox()
        self.margin_ratio_spin.setRange(0.1, 20.0)
        self.margin_ratio_spin.setSingleStep(0.1)
        self.margin_ratio_spin.setDecimals(2)
        self.margin_ratio_spin.setSuffix("%")
        self.bottom_margin_ratio_spin = QDoubleSpinBox()
        self.bottom_margin_ratio_spin.setRange(0.1, 20.0)
        self.bottom_margin_ratio_spin.setSingleStep(0.1)
        self.bottom_margin_ratio_spin.setDecimals(2)
        self.bottom_margin_ratio_spin.setSuffix("%")
        style_form.addRow("\u65e5\u671f\u683c\u5f0f", self.date_format_combo)
        style_form.addRow("\u524d\u7f00", self.prefix_edit)
        style_form.addRow("\u540e\u7f00", self.suffix_edit)
        style_form.addRow("\u5b57\u4f53", font_row)
        style_form.addRow("\u989c\u8272", color_row)
        style_form.addRow("\u900f\u660e\u5ea6", self.opacity_spin)
        style_form.addRow("\u5b57\u4f53\u6bd4\u4f8b", self.font_ratio_spin)
        style_form.addRow("\u53f3\u8fb9\u8ddd\u6bd4\u4f8b", self.margin_ratio_spin)
        style_form.addRow("\u4e0b\u8fb9\u8ddd\u6bd4\u4f8b", self.bottom_margin_ratio_spin)

        second_line_group = QGroupBox("\u7b2c\u4e8c\u884c\u6a21\u5f0f")
        second_line_form = QFormLayout(second_line_group)
        self.second_line_mode_combo = QComboBox()
        self.second_line_mode_combo.addItem("\u5173\u95ed", "off")
        self.second_line_mode_combo.addItem("\u7eaa\u5ff5\u65e5", "anniversary")
        self.second_line_mode_combo.addItem("\u751f\u65e5", "birthday")
        self.second_line_mode_combo.addItem("\u81ea\u5b9a\u4e49", "custom")
        self.occasion_prefix_edit = QLineEdit()
        self.occasion_date_edit = QDateEdit()
        self.occasion_date_edit.setCalendarPopup(True)
        self.occasion_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.custom_text_edit = QLineEdit()
        second_line_form.addRow("\u6a21\u5f0f", self.second_line_mode_combo)
        second_line_form.addRow("\u524d\u7f00\u6587\u672c", self.occasion_prefix_edit)
        second_line_form.addRow("\u53c2\u8003\u65e5\u671f", self.occasion_date_edit)
        second_line_form.addRow("\u81ea\u5b9a\u4e49\u6587\u672c", self.custom_text_edit)

        output_group = QGroupBox("\u8f93\u51fa\u8bbe\u7f6e")
        output_form = QFormLayout(output_group)
        self.output_dir_edit = QLineEdit()
        self.failed_dir_edit = QLineEdit()
        output_form.addRow("\u6210\u529f\u76ee\u5f55\u540d", self.output_dir_edit)
        output_form.addRow("\u5931\u8d25\u76ee\u5f55\u540d", self.failed_dir_edit)

        settings_layout.addWidget(source_group)
        settings_layout.addWidget(style_group)
        settings_layout.addWidget(second_line_group)
        settings_layout.addWidget(output_group)
        settings_layout.addStretch(1)

        self.preview_text_label = QLabel("\u5f53\u524d\u6c34\u5370\u6587\u672c\uff1a")
        self.preview_text_label.setWordWrap(True)
        self.preview_source_label = QLabel("\u65e5\u671f\u6765\u6e90\u8bf4\u660e\uff1a")
        self.preview_source_label.setWordWrap(True)
        preview_nav = QHBoxLayout()
        self.preview_prev_button = QPushButton("\u4e0a\u4e00\u5f20")
        self.preview_next_button = QPushButton("\u4e0b\u4e00\u5f20")
        self.preview_index_label = QLabel("0 / 0")
        preview_nav.addWidget(self.preview_prev_button)
        preview_nav.addWidget(self.preview_next_button)
        preview_nav.addWidget(self.preview_index_label)
        preview_nav.addStretch(1)
        preview_layout.addWidget(self.preview_text_label)
        preview_layout.addWidget(self.preview_source_label)
        preview_layout.addLayout(preview_nav)

        self.watermarked_image_label = QLabel("\u6c34\u5370\u9884\u89c8")
        self.watermarked_image_label.setAlignment(Qt.AlignCenter)
        self.watermarked_image_label.setMinimumSize(520, 420)
        self.watermarked_image_label.setStyleSheet("border: 1px solid #999; background: #222; color: #ddd;")
        preview_layout.addWidget(self.watermarked_image_label, 1)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        preview_layout.addWidget(self.result_text)

        footer = QHBoxLayout()
        self.red_packet_button = QPushButton("\u9886\u4e2a\u7ea2\u5305")
        self.support_author_button = QPushButton("\u652f\u6301\u4f5c\u8005")
        footer.addWidget(self.red_packet_button)
        footer.addWidget(self.support_author_button)
        footer.addStretch(1)
        root_layout.addLayout(footer)

        self.select_files_button.clicked.connect(self._select_files)
        self.select_folder_button.clicked.connect(self._select_folder)
        self.process_button.clicked.connect(self._process_selected)
        self.open_output_button.clicked.connect(self._open_output_dir)
        self.save_settings_button.clicked.connect(self._save_settings_dialog)
        self.load_settings_button.clicked.connect(self._load_settings_dialog)
        self.font_path_button.clicked.connect(self._choose_font)
        self.color_button.clicked.connect(self._choose_color)
        self.fallback_checkbox.toggled.connect(self._on_fallback_toggled)
        self.second_line_mode_combo.currentIndexChanged.connect(self._on_second_line_mode_changed)
        self.preview_prev_button.clicked.connect(self._show_previous_preview)
        self.preview_next_button.clicked.connect(self._show_next_preview)
        self.red_packet_button.clicked.connect(
            lambda: self._show_support_dialog(
                "\u9886\u4e2a\u7ea2\u5305",
                "\u5982\u679c\u8fd9\u4e2a\u5c0f\u5de5\u5177\u521a\u597d\u5e2e\u5230\u4f60\uff0c\u6b22\u8fce\u9886\u4e2a\u5c0f\u7ea2\u5305\uff0c\u4e5f\u8c22\u8c22\u4f60\u7684\u559c\u6b22\u3002",
                "RED_PACKET_JPG",
            )
        )
        self.support_author_button.clicked.connect(
            lambda: self._show_support_dialog(
                "\u652f\u6301\u4f5c\u8005",
                "\u5982\u679c\u4f60\u613f\u610f\u652f\u6301\u8fd9\u4e2a\u5de5\u5177\u7ee7\u7eed\u66f4\u65b0\uff0c\u53ef\u4ee5\u626b\u7801\u652f\u6301\u4f5c\u8005\uff0c\u611f\u8c22\u4f60\u7684\u8ba4\u53ef\u3002",
                "SUPPORT_QR_PNG",
            )
        )

        refresh_widgets = (
            self.date_source_combo,
            self.unified_date_edit,
            self.date_format_combo,
            self.prefix_edit,
            self.suffix_edit,
            self.font_path_edit,
            self.opacity_spin,
            self.font_ratio_spin,
            self.margin_ratio_spin,
            self.bottom_margin_ratio_spin,
            self.output_dir_edit,
            self.failed_dir_edit,
            self.second_line_mode_combo,
            self.occasion_prefix_edit,
            self.occasion_date_edit,
            self.custom_text_edit,
            self.fallback_checkbox,
        )
        for widget in refresh_widgets:
            self._connect_refresh(widget)

    def _connect_refresh(self, widget: QWidget) -> None:
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self._refresh_preview)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._refresh_preview)
        elif isinstance(widget, QDateEdit):
            widget.dateChanged.connect(self._refresh_preview)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self._refresh_preview)
        else:
            widget.toggled.connect(self._refresh_preview)  # type: ignore[attr-defined]

    def _load_settings_to_ui(self) -> None:
        snapshot = self.settings
        widgets = [
            self.date_source_combo,
            self.unified_date_edit,
            self.fallback_checkbox,
            self.date_format_combo,
            self.prefix_edit,
            self.suffix_edit,
            self.font_path_edit,
            self.opacity_spin,
            self.font_ratio_spin,
            self.margin_ratio_spin,
            self.bottom_margin_ratio_spin,
            self.output_dir_edit,
            self.failed_dir_edit,
            self.second_line_mode_combo,
            self.occasion_prefix_edit,
            self.occasion_date_edit,
            self.custom_text_edit,
        ]
        previous_states = [widget.blockSignals(True) for widget in widgets]
        self._is_loading_settings = True
        try:
            self.date_source_combo.setCurrentText("\u7edf\u4e00\u6307\u5b9a\u65e5\u671f" if snapshot.use_unified_date else "EXIF")
            unified = snapshot.unified_date or date.today()
            self.unified_date_edit.setDate(QDate(unified.year, unified.month, unified.day))
            self.fallback_checkbox.setChecked(snapshot.use_file_mtime_fallback)
            self.date_format_combo.setCurrentText(snapshot.date_format)
            self.prefix_edit.setText(snapshot.prefix)
            self.suffix_edit.setText(snapshot.suffix)
            self.font_path_edit.setText(snapshot.font_path)
            self.opacity_spin.setValue(int(round(snapshot.opacity * 100)))
            self.font_ratio_spin.setValue(snapshot.font_size_ratio * 100)
            self.margin_ratio_spin.setValue(snapshot.margin_ratio * 100)
            self.bottom_margin_ratio_spin.setValue(snapshot.bottom_margin_ratio * 100)
            self.output_dir_edit.setText(snapshot.output_dir_name)
            self.failed_dir_edit.setText(snapshot.failed_dir_name)
            self._set_second_line_mode(snapshot.second_line_mode)
            self.occasion_prefix_edit.setText(snapshot.occasion_prefix)
            occasion = snapshot.occasion_date or date.today()
            self.occasion_date_edit.setDate(QDate(occasion.year, occasion.month, occasion.day))
            self.custom_text_edit.setText(snapshot.custom_text)
            self._update_color_preview(snapshot.color_rgb)
            self._update_second_line_fields()
        finally:
            self._is_loading_settings = False
            for widget, previous in zip(widgets, previous_states):
                widget.blockSignals(previous)

    def _set_second_line_mode(self, mode: str) -> None:
        index = max(0, self.second_line_mode_combo.findData(mode))
        self.second_line_mode_combo.setCurrentIndex(index)

    def _current_second_line_mode(self) -> str:
        return str(self.second_line_mode_combo.currentData())

    def _update_second_line_fields(self) -> None:
        mode = self._current_second_line_mode()
        needs_prefix_and_date = mode in {"anniversary", "birthday"}
        self.occasion_prefix_edit.setVisible(needs_prefix_and_date)
        self.occasion_date_edit.setVisible(needs_prefix_and_date)
        self.custom_text_edit.setVisible(mode == "custom")

        form = self.occasion_prefix_edit.parentWidget().layout()
        if isinstance(form, QFormLayout):
            prefix_label = form.labelForField(self.occasion_prefix_edit)
            date_label = form.labelForField(self.occasion_date_edit)
            custom_label = form.labelForField(self.custom_text_edit)
            if prefix_label:
                prefix_label.setVisible(needs_prefix_and_date)
            if date_label:
                date_label.setVisible(needs_prefix_and_date)
                date_label.setText("\u53c2\u8003\u65e5\u671f" if mode == "anniversary" else "\u751f\u65e5\u65e5\u671f")
            if custom_label:
                custom_label.setVisible(mode == "custom")

    def _read_settings_from_ui(self) -> AppSettings:
        settings = AppSettings.spec_defaults()
        settings.use_unified_date = self.date_source_combo.currentText() == "\u7edf\u4e00\u6307\u5b9a\u65e5\u671f"
        settings.unified_date = self.unified_date_edit.date().toPython() if settings.use_unified_date else None
        settings.use_file_mtime_fallback = self.fallback_checkbox.isChecked()
        settings.date_format = self.date_format_combo.currentText()
        settings.prefix = self.prefix_edit.text()
        settings.suffix = self.suffix_edit.text()
        settings.font_path = self.font_path_edit.text().strip() or AppSettings.spec_defaults().font_path
        settings.color_rgb = tuple(self.color_preview.property("rgb") or (233, 110, 37))
        settings.opacity = self.opacity_spin.value() / 100.0
        settings.font_size_ratio = self.font_ratio_spin.value() / 100.0
        settings.margin_ratio = self.margin_ratio_spin.value() / 100.0
        settings.bottom_margin_ratio = self.bottom_margin_ratio_spin.value() / 100.0
        settings.output_dir_name = self.output_dir_edit.text().strip() or "dated_output"
        settings.failed_dir_name = self.failed_dir_edit.text().strip() or "dated_failed"
        settings.second_line_mode = self._current_second_line_mode()
        settings.occasion_prefix = self.occasion_prefix_edit.text()
        settings.occasion_date = self.occasion_date_edit.date().toPython() if settings.second_line_mode in {"anniversary", "birthday"} else None
        settings.custom_text = self.custom_text_edit.text() if settings.second_line_mode == "custom" else ""
        return settings

    def _current_preview_path(self) -> Path | None:
        if not self.selected_paths:
            return None
        return self.selected_paths[self.preview_index]

    def _update_preview_navigation(self) -> None:
        total = len(self.selected_paths)
        if total == 0:
            self.preview_index = 0
            self.preview_index_label.setText("0 / 0")
            self.preview_prev_button.setEnabled(False)
            self.preview_next_button.setEnabled(False)
            self.preview_file_label.setText("\u9884\u89c8\u6587\u4ef6\uff1a\u65e0")
            return

        self.preview_index %= total
        self.preview_index_label.setText(f"{self.preview_index + 1} / {total}")
        can_switch = total > 1
        self.preview_prev_button.setEnabled(can_switch)
        self.preview_next_button.setEnabled(can_switch)
        self.preview_file_label.setText(f"\u9884\u89c8\u6587\u4ef6\uff1a{self.selected_paths[self.preview_index].name}")

    def _show_previous_preview(self) -> None:
        if not self.selected_paths:
            return
        self.preview_index = (self.preview_index - 1) % len(self.selected_paths)
        self._refresh_preview()

    def _show_next_preview(self) -> None:
        if not self.selected_paths:
            return
        self.preview_index = (self.preview_index + 1) % len(self.selected_paths)
        self._refresh_preview()

    def _select_files(self) -> None:
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "\u9009\u62e9 JPG/JPEG \u6587\u4ef6",
            "",
            "JPEG Images (*.jpg *.jpeg *.JPG *.JPEG)",
        )
        if not filenames:
            return
        self.selected_paths = [Path(name) for name in filenames]
        self.selection_root = determine_root(self.selected_paths)
        self.preview_index = 0
        self._after_selection()

    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "\u9009\u62e9\u6587\u4ef6\u5939")
        if not folder:
            return
        folder_path = Path(folder)
        self.selected_paths = collect_jpegs(folder_path)
        self.selection_root = folder_path
        self.preview_index = 0
        if not self.selected_paths:
            QMessageBox.warning(self, "\u672a\u627e\u5230\u56fe\u7247", "\u6240\u9009\u6587\u4ef6\u5939\u53ca\u5176\u5b50\u6587\u4ef6\u5939\u4e2d\u6ca1\u6709 JPG/JPEG \u6587\u4ef6\u3002")
        self._after_selection()

    def _after_selection(self) -> None:
        self.status_label.setText(f"\u5df2\u9009\u56fe\u7247\uff1a{len(self.selected_paths)}")
        self._update_preview_navigation()
        self._refresh_preview()

    def _on_fallback_toggled(self, checked: bool) -> None:
        if checked:
            QMessageBox.information(
                self,
                "\u63d0\u793a",
                "\u542f\u7528\u540e\uff0c\u7f3a\u5c11 EXIF \u7684\u7167\u7247\u5c06\u4e0d\u518d\u8fdb\u5165\u5931\u8d25\u76ee\u5f55\uff0c\u800c\u662f\u4f7f\u7528\u6587\u4ef6\u4fee\u6539\u65e5\u671f\u751f\u6210\u6c34\u5370\u3002\u8fd9\u6837\u53ef\u80fd\u4e0e\u5b9e\u9645\u62cd\u6444\u65e5\u671f\u4e0d\u4e00\u81f4\u3002",
            )

    def _on_second_line_mode_changed(self) -> None:
        self._update_second_line_fields()
        self._refresh_preview()

    def _choose_font(self) -> None:
        library_dir = Path.cwd() / "\u5b57\u4f53\u5e93"
        start_dir = str(library_dir if library_dir.exists() else Path.cwd())
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "\u9009\u62e9\u5b57\u4f53",
            start_dir,
            "Fonts (*.ttf *.ttc *.otf)",
        )
        if filename:
            self.font_path_edit.setText(filename)

    def _choose_color(self) -> None:
        current = QColor(*self.settings.color_rgb)
        color = QColorDialog.getColor(current, self, "\u9009\u62e9\u6c34\u5370\u989c\u8272")
        if color.isValid():
            self._update_color_preview((color.red(), color.green(), color.blue()))
            self._refresh_preview()

    def _update_color_preview(self, rgb: tuple[int, int, int]) -> None:
        self.color_preview.setProperty("rgb", rgb)
        self.color_preview.setStyleSheet(f"background: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border: 1px solid #555;")

    def _refresh_preview(self) -> None:
        if self._is_loading_settings:
            return
        self.settings = self._read_settings_from_ui()
        self._update_preview_navigation()
        if not self.selected_paths:
            self.preview_text_label.setText("\u5f53\u524d\u6c34\u5370\u6587\u672c\uff1a")
            self.preview_source_label.setText("\u65e5\u671f\u6765\u6e90\u8bf4\u660e\uff1a")
            self.watermarked_image_label.setText("\u6c34\u5370\u9884\u89c8")
            self.watermarked_image_label.setPixmap(QPixmap())
            return

        preview_path = self._current_preview_path()
        if preview_path is None:
            return
        try:
            preview = build_preview(preview_path, self.settings)
            self.preview_text_label.setText(f"\u5f53\u524d\u6c34\u5370\u6587\u672c\uff1a\n{preview.text}")
            self.preview_source_label.setText(f"\u65e5\u671f\u6765\u6e90\u8bf4\u660e\uff1a{preview.source_label}")
            qt_image = ImageQt(preview.preview_image)
            self._set_preview_pixmap(self.watermarked_image_label, QPixmap.fromImage(qt_image))
            self.result_text.setPlainText("")
        except Exception as exc:
            self.preview_text_label.setText("\u5f53\u524d\u6c34\u5370\u6587\u672c\uff1a\u9884\u89c8\u5931\u8d25")
            self.preview_source_label.setText(f"\u65e5\u671f\u6765\u6e90\u8bf4\u660e\uff1a{exc}")
            self.watermarked_image_label.setPixmap(QPixmap())
            self.watermarked_image_label.setText("\u6c34\u5370\u9884\u89c8\u5931\u8d25")

    def _set_preview_pixmap(self, label: QLabel, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled)
        label.setText("")

    def _load_embedded_support_pixmap(self, asset_name: str) -> QPixmap:
        encoded = getattr(embedded_assets, asset_name, "")
        if not encoded:
            raise ValueError(asset_name)
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(encoded))
        return pixmap

    def _show_support_dialog(self, title: str, message: str, asset_name: str) -> None:
        try:
            pixmap = self._load_embedded_support_pixmap(asset_name)
        except Exception:
            QMessageBox.warning(self, "\u63d0\u793a", f"\u672a\u627e\u5230\u5185\u5d4c\u56fe\u7247\u8d44\u6e90\uff1a{asset_name}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(420, 560)
        layout = QVBoxLayout(dialog)

        text_label = QLabel(message)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(pixmap.scaled(360, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(image_label, 1)

        close_button = QPushButton("\u5173\u95ed")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self.selected_paths:
            self._refresh_preview()

    def _save_settings_dialog(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "\u4fdd\u5b58\u8bbe\u7f6e",
            str(Path.cwd() / "watermark_settings.json"),
            "JSON Files (*.json)",
        )
        if not filename:
            return
        self.settings = self._read_settings_from_ui()
        save_settings(Path(filename), self.settings)
        self.result_text.setPlainText(f"\u5df2\u4fdd\u5b58\u8bbe\u7f6e\u5230\uff1a{filename}")

    def _load_settings_dialog(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "\u52a0\u8f7d\u8bbe\u7f6e", str(Path.cwd()), "JSON Files (*.json)")
        if not filename:
            return
        self.settings = load_settings(Path(filename))
        self._load_settings_to_ui()
        self._refresh_preview()
        self.result_text.setPlainText(f"\u5df2\u52a0\u8f7d\u8bbe\u7f6e\uff1a{filename}")

    def _process_selected(self) -> None:
        if not self.selected_paths or self.selection_root is None:
            QMessageBox.warning(self, "\u672a\u9009\u62e9\u56fe\u7247", "\u8bf7\u5148\u9009\u62e9\u591a\u4e2a\u6587\u4ef6\u6216\u4e00\u4e2a\u6587\u4ef6\u5939\u3002")
            return

        self.settings = self._read_settings_from_ui()
        results, report_path = process_files(self.selection_root, self.selected_paths, self.settings)

        success_count = sum(1 for item in results if item.status == "success")
        failed_count = sum(1 for item in results if item.status == "failed")
        missing_exif_count = sum(1 for item in results if "EXIF" in item.reason)
        lines = [
            f"\u6210\u529f\uff1a{success_count}",
            f"\u5931\u8d25\uff1a{failed_count}",
            f"\u7f3a\u5c11 EXIF\uff1a{missing_exif_count}",
            f"\u62a5\u544a\uff1a{report_path}",
        ]
        if failed_count:
            lines.extend(["", "\u5931\u8d25\u660e\u7ec6\uff1a"])
            for item in results:
                if item.status == "failed":
                    lines.append(f"{item.source_path} -> {item.reason}")
        self.result_text.setPlainText("\n".join(lines))
        QMessageBox.information(
            self,
            "\u5904\u7406\u5b8c\u6210",
            f"\u6210\u529f {success_count} \u5f20\uff0c\u5931\u8d25 {failed_count} \u5f20\uff0c\u7f3a\u5c11 EXIF {missing_exif_count} \u5f20\u3002",
        )

    def _open_output_dir(self) -> None:
        if self.selection_root is None:
            QMessageBox.information(self, "\u63d0\u793a", "\u8fd8\u6ca1\u6709\u53ef\u6253\u5f00\u7684\u8f93\u51fa\u76ee\u5f55\u3002")
            return
        output_dir = self.selection_root / self._read_settings_from_ui().output_dir_name
        if not output_dir.exists():
            QMessageBox.information(self, "\u63d0\u793a", f"\u8f93\u51fa\u76ee\u5f55\u4e0d\u5b58\u5728\uff1a{output_dir}")
            return
        os.startfile(str(output_dir))  # type: ignore[attr-defined]
