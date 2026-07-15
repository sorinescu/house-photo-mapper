"""Tests for ReportProgressDialog — progress display during report generation."""

import pytest
from PySide6.QtWidgets import QApplication, QProgressBar, QPushButton, QLabel

from house_photo_mapper.presentation.views.report_progress import ReportProgressDialog


class TestReportProgressDialog:
    """Tests for ReportProgressDialog widget."""

    def test_dialog_creation(self, qapp: QApplication) -> None:
        """Dialog creates with correct window title and modal."""
        dialog = ReportProgressDialog(total_pages=10)
        assert dialog.windowTitle() == "Generating Report"
        assert dialog.isModal()

    def test_has_progress_bar(self, qapp: QApplication) -> None:
        """Dialog contains a QProgressBar."""
        dialog = ReportProgressDialog(total_pages=10)
        progress_bar = dialog.findChild(QProgressBar)
        assert progress_bar is not None
        assert progress_bar.maximum() == 10

    def test_has_cancel_button(self, qapp: QApplication) -> None:
        """Dialog has a Cancel button that is enabled initially."""
        dialog = ReportProgressDialog(total_pages=10)
        cancel_btn = dialog.findChild(QPushButton)
        assert cancel_btn is not None
        assert cancel_btn.isEnabled()

    def test_initial_label_text(self, qapp: QApplication) -> None:
        """Dialog shows initial page count label."""
        dialog = ReportProgressDialog(total_pages=10)
        labels = dialog.findChildren(QLabel)
        # Should have a label with "Generating page 0 of 10"
        page_label = None
        for label in labels:
            if "Generating page" in label.text():
                page_label = label
                break
        assert page_label is not None
        assert "0 of 10" in page_label.text()

    def test_update_progress(self, qapp: QApplication) -> None:
        """update_progress updates the progress bar and label."""
        dialog = ReportProgressDialog(total_pages=10)
        dialog.update_progress(5, 10)

        progress_bar = dialog.findChild(QProgressBar)
        assert progress_bar is not None
        assert progress_bar.value() == 5

        labels = dialog.findChildren(QLabel)
        page_label = None
        for label in labels:
            if "Generating page" in label.text():
                page_label = label
                break
        assert page_label is not None
        assert "5 of 10" in page_label.text()

    def test_cancel_button_disabled_after_cancel(self, qapp: QApplication) -> None:
        """Cancel button is disabled after clicking Cancel."""
        dialog = ReportProgressDialog(total_pages=10)
        cancel_btn = dialog.findChild(QPushButton)
        assert cancel_btn is not None

        cancel_btn.click()
        assert not cancel_btn.isEnabled()

    def test_was_cancelled(self, qapp: QApplication) -> None:
        """was_cancelled returns True after Cancel is clicked."""
        dialog = ReportProgressDialog(total_pages=10)
        assert not dialog.was_cancelled()

        cancel_btn = dialog.findChild(QPushButton)
        cancel_btn.click()
        assert dialog.was_cancelled()

    def test_finish_closes_dialog(self, qapp: QApplication) -> None:
        """finish() accepts (closes) the dialog."""
        dialog = ReportProgressDialog(total_pages=10)
        dialog.show()
        assert dialog.isVisible()

        dialog.finish()
        assert dialog.result() == ReportProgressDialog.DialogCode.Accepted
