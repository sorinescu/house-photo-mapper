"""ReportProgressDialog — Shows progress during background PDF report generation.

Displays a QProgressBar with current/total page count and a Cancel button.
Connected to ReportViewModel.progress and finished signals.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ReportProgressDialog(QDialog):
    """Dialog showing progress during report generation.

    Displays a progress bar and page count label, with a Cancel button
    to abort the generation process.

    Attributes:
        total_pages: Total number of pages being generated.
    """

    def __init__(
        self,
        total_pages: int,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize ReportProgressDialog.

        Args:
            total_pages: Total number of pages in the report.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._total_pages = total_pages
        self._cancelled = False

        self.setWindowTitle("Generating Report")
        self.setModal(True)
        self.setMinimumWidth(350)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog layout."""
        layout = QVBoxLayout(self)

        # Header label
        self._header_label = QLabel("Generating report...")
        layout.addWidget(self._header_label)

        # Progress bar
        from PySide6.QtWidgets import QProgressBar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(self._total_pages)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Page count label
        self._page_label = QLabel(
            f"Generating page 0 of {self._total_pages}"
        )
        layout.addWidget(self._page_label)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    @Slot()
    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self._cancelled = True
        self._cancel_btn.setEnabled(False)
        self._page_label.setText("Cancelling...")

    @Slot(int, int)
    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar and label.

        Args:
            current: Current page number (1-based).
            total: Total number of pages.
        """
        self._progress_bar.setValue(current)
        self._page_label.setText(f"Generating page {current} of {total}")

    def finish(self) -> None:
        """Close the dialog by accepting it."""
        self.accept()

    def was_cancelled(self) -> bool:
        """Return whether the user cancelled generation.

        Returns:
            True if Cancel was clicked, False otherwise.
        """
        return self._cancelled
