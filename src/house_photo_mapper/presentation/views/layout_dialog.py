"""LayoutDialog — Page format and orientation selection for report generation.

Simple dialog with two QComboBox widgets for selecting page format
(A4, US Letter) and orientation (Portrait, Landscape).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QPushButton,
    QWidget,
)


class LayoutDialog(QDialog):
    """Dialog for selecting report page format and orientation.

    Provides two combo boxes:
    - Format: A4, US Letter
    - Orientation: Portrait, Landscape

    Returns dialog result (Accepted/Rejected) and provides
    get_selected_layout() and get_page_size_string() for reading selections.
    """

    def __init__(self, parent=None) -> None:
        """Initialize LayoutDialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Report Layout")
        self.setMinimumSize(350, 250)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Page format group
        group = QGroupBox("Page Format")
        form_layout = QFormLayout()

        # Format combo
        self._format_combo = QComboBox()
        self._format_combo.setObjectName("format_combo")
        self._format_combo.addItems(["A4", "US Letter"])
        form_layout.addRow("Format:", self._format_combo)

        # Orientation combo
        self._orientation_combo = QComboBox()
        self._orientation_combo.setObjectName("orientation_combo")
        self._orientation_combo.addItems(["Portrait", "Landscape"])
        form_layout.addRow("Orientation:", self._orientation_combo)

        group.setLayout(form_layout)
        layout.addWidget(group)

        # Buttons
        button_layout = QHBoxLayout()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancel_button")
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()

        self._ok_btn = QPushButton("OK")
        self._ok_btn.setObjectName("ok_button")
        button_layout.addWidget(self._ok_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect button signals."""
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)

    def get_selected_layout(self) -> tuple[str, str]:
        """Get the currently selected format and orientation.

        Returns:
            Tuple of (format, orientation) strings.
        """
        return (self._format_combo.currentText(), self._orientation_combo.currentText())

    def get_page_size_string(self) -> str:
        """Get formatted page size string from current selections.

        Returns:
            String like "A4 Portrait", "A4 Landscape", "US Letter Portrait", etc.
        """
        fmt, orient = self.get_selected_layout()
        if fmt == "US Letter":
            return f"US Letter {orient}"
        return f"{fmt} {orient}"
