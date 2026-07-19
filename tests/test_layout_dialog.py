"""Tests for ReportConfigDialog — combined report layout and color settings UI."""

import pytest
from PySide6.QtWidgets import QApplication, QComboBox, QPushButton

from house_photo_mapper.presentation.views.layout_dialog import ReportConfigDialog


class TestReportConfigDialog:
    """Tests for ReportConfigDialog widget."""

    def test_dialog_creation(self, qapp: QApplication) -> None:
        """Dialog creates with correct window title."""
        dialog = ReportConfigDialog()
        assert dialog.windowTitle() == "Generate Report"

    def test_default_selection(self, qapp: QApplication) -> None:
        """Default selection is A4 Portrait with original colors."""
        dialog = ReportConfigDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")
        mode_combo = dialog.findChild(QComboBox, "mode_combo")

        assert format_combo is not None
        assert orientation_combo is not None
        assert mode_combo is not None
        assert format_combo.currentText() == "A4"
        assert orientation_combo.currentText() == "Portrait"
        assert mode_combo.currentIndex() == 0

    def test_custom_initial_state(self, qapp: QApplication) -> None:
        """Dialog accepts custom initial format, orientation, and color mode."""
        dialog = ReportConfigDialog(
            current_format="US Letter",
            current_orientation="Landscape",
            current_color_mode="override",
            current_color="#FF0000",
        )
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")
        mode_combo = dialog.findChild(QComboBox, "mode_combo")

        assert format_combo.currentText() == "US Letter"
        assert orientation_combo.currentText() == "Landscape"
        assert mode_combo.currentIndex() == 1
        assert dialog.get_selected_color() == "#FF0000"

    def test_get_layout(self, qapp: QApplication) -> None:
        """get_selected_layout returns correct (format, orientation) tuple."""
        dialog = ReportConfigDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")

        format_combo.setCurrentText("US Letter")
        orientation_combo.setCurrentText("Landscape")

        fmt, orient = dialog.get_selected_layout()
        assert fmt == "US Letter"
        assert orient == "Landscape"

    def test_ok_button(self, qapp: QApplication) -> None:
        """Clicking OK accepts the dialog."""
        dialog = ReportConfigDialog()
        ok_btn = dialog.findChild(QPushButton, "ok_button")
        assert ok_btn is not None

        ok_btn.click()
        assert dialog.result() == ReportConfigDialog.DialogCode.Accepted

    def test_cancel_button(self, qapp: QApplication) -> None:
        """Clicking Cancel rejects the dialog."""
        dialog = ReportConfigDialog()
        cancel_btn = dialog.findChild(QPushButton, "cancel_button")
        assert cancel_btn is not None

        cancel_btn.click()
        assert dialog.result() == ReportConfigDialog.DialogCode.Rejected

    def test_get_page_size_string_portrait(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'A4 Portrait' for default."""
        dialog = ReportConfigDialog()
        result = dialog.get_page_size_string()
        assert result == "A4 Portrait"

    def test_get_page_size_string_landscape(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'A4 Landscape' for A4+Landscape."""
        dialog = ReportConfigDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")
        orientation_combo.setCurrentText("Landscape")

        result = dialog.get_page_size_string()
        assert result == "A4 Landscape"

    def test_get_page_size_string_us_letter(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'US Letter' for US Letter+Portrait."""
        dialog = ReportConfigDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        format_combo.setCurrentText("US Letter")

        result = dialog.get_page_size_string()
        assert result == "US Letter Portrait"

    def test_color_mode_original(self, qapp: QApplication) -> None:
        """get_selected_color_mode returns 'original' by default."""
        dialog = ReportConfigDialog()
        assert dialog.get_selected_color_mode() == "original"

    def test_color_mode_override(self, qapp: QApplication) -> None:
        """get_selected_color_mode returns 'override' when override selected."""
        dialog = ReportConfigDialog(current_color_mode="override")
        assert dialog.get_selected_color_mode() == "override"

    def test_color_controls_disabled_by_default(self, qapp: QApplication) -> None:
        """Color picker controls are disabled when original mode is selected."""
        dialog = ReportConfigDialog()
        assert not dialog._color_btn.isEnabled()
        assert not dialog._color_preview.isEnabled()
        assert not dialog._color_hex.isEnabled()

    def test_color_controls_enabled_in_override(self, qapp: QApplication) -> None:
        """Color picker controls are enabled when override mode is selected."""
        dialog = ReportConfigDialog(current_color_mode="override")
        assert dialog._color_btn.isEnabled()
        assert dialog._color_preview.isEnabled()
        assert dialog._color_hex.isEnabled()

    def test_mode_change_toggles_color_controls(self, qapp: QApplication) -> None:
        """Changing mode combo toggles color control enabled state."""
        dialog = ReportConfigDialog()
        mode_combo = dialog.findChild(QComboBox, "mode_combo")

        # Switch to override
        mode_combo.setCurrentIndex(1)
        assert dialog._color_btn.isEnabled()

        # Switch back to original
        mode_combo.setCurrentIndex(0)
        assert not dialog._color_btn.isEnabled()
