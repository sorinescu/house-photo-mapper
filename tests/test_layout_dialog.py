"""Tests for LayoutDialog — page format and orientation selection UI."""

import pytest
from PySide6.QtWidgets import QApplication, QComboBox, QPushButton

from house_photo_mapper.presentation.views.layout_dialog import LayoutDialog


class TestLayoutDialog:
    """Tests for LayoutDialog widget."""

    def test_dialog_creation(self, qapp: QApplication) -> None:
        """Dialog creates with correct window title."""
        dialog = LayoutDialog()
        assert dialog.windowTitle() == "Report Layout"

    def test_default_selection(self, qapp: QApplication) -> None:
        """Default selection is A4 Portrait."""
        dialog = LayoutDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")

        assert format_combo is not None
        assert orientation_combo is not None
        assert format_combo.currentText() == "A4"
        assert orientation_combo.currentText() == "Portrait"

    def test_get_layout(self, qapp: QApplication) -> None:
        """get_selected_layout returns correct (format, orientation) tuple."""
        dialog = LayoutDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")

        # Change selections
        format_combo.setCurrentText("US Letter")
        orientation_combo.setCurrentText("Landscape")

        fmt, orient = dialog.get_selected_layout()
        assert fmt == "US Letter"
        assert orient == "Landscape"

    def test_ok_button(self, qapp: QApplication) -> None:
        """Clicking OK accepts the dialog."""
        dialog = LayoutDialog()
        ok_btn = dialog.findChild(QPushButton, "ok_button")
        assert ok_btn is not None

        ok_btn.click()
        assert dialog.result() == LayoutDialog.DialogCode.Accepted

    def test_cancel_button(self, qapp: QApplication) -> None:
        """Clicking Cancel rejects the dialog."""
        dialog = LayoutDialog()
        cancel_btn = dialog.findChild(QPushButton, "cancel_button")
        assert cancel_btn is not None

        cancel_btn.click()
        assert dialog.result() == LayoutDialog.DialogCode.Rejected

    def test_get_page_size_string_portrait(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'A4 Portrait' for default."""
        dialog = LayoutDialog()
        result = dialog.get_page_size_string()
        assert result == "A4 Portrait"

    def test_get_page_size_string_landscape(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'A4 Landscape' for A4+Landscape."""
        dialog = LayoutDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        orientation_combo = dialog.findChild(QComboBox, "orientation_combo")
        orientation_combo.setCurrentText("Landscape")

        result = dialog.get_page_size_string()
        assert result == "A4 Landscape"

    def test_get_page_size_string_us_letter(self, qapp: QApplication) -> None:
        """get_page_size_string returns 'US Letter' for US Letter+Portrait."""
        dialog = LayoutDialog()
        format_combo = dialog.findChild(QComboBox, "format_combo")
        format_combo.setCurrentText("US Letter")

        result = dialog.get_page_size_string()
        assert result == "US Letter Portrait"
