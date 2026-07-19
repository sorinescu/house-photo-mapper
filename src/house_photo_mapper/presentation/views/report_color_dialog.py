"""ReportColorDialog — Annotation color configuration for report generation.

Simple dialog with a combo box for selecting between original annotation colors
and a user-selected override color for PDF exports.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ReportColorDialog(QDialog):
    """Dialog for selecting report annotation color mode.

    Provides a combo box to choose between original annotation colors
    and a custom override color, with a color picker button.

    Returns dialog result (Accepted/Rejected) and provides
    get_selected_mode() and get_selected_color() for reading selections.
    """

    def __init__(
        self,
        current_mode: str = "original",
        current_color: str = "#DC2828",
        parent=None,
    ) -> None:
        """Initialize ReportColorDialog.

        Args:
            current_mode: Initial mode ("original" or "override").
            current_color: Initial override color hex string.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Report Colors")
        self.setMinimumSize(350, 200)

        self._current_color = current_color

        self._setup_ui(current_mode)
        self._connect_signals()

        # Set initial state based on mode
        self._update_color_controls(current_mode == "override")

    def _setup_ui(self, current_mode: str) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Annotation Colors group
        group = QGroupBox("Annotation Colors")
        form_layout = QFormLayout()

        # Mode combo
        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("mode_combo")
        self._mode_combo.addItems(["Use original colors", "Override with custom color"])
        if current_mode == "override":
            self._mode_combo.setCurrentIndex(1)
        form_layout.addRow("Colors:", self._mode_combo)

        # Color preview and picker button
        color_row = QHBoxLayout()

        self._color_preview = QLabel()
        self._color_preview.setObjectName("color_preview")
        self._color_preview.setFixedSize(24, 24)
        self._color_preview.setStyleSheet(
            f"background-color: {self._current_color}; border: 1px solid gray;"
        )
        color_row.addWidget(self._color_preview)

        self._color_hex = QLabel(self._current_color)
        self._color_hex.setObjectName("color_hex")
        color_row.addWidget(self._color_hex)

        color_row.addStretch()

        self._color_btn = QPushButton("Choose Color...")
        self._color_btn.setObjectName("choose_color_button")
        self._color_btn.clicked.connect(self._choose_color)
        color_row.addWidget(self._color_btn)

        form_layout.addRow("Override:", color_row)

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
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)

    @Slot(int)
    def _on_mode_changed(self, index: int) -> None:
        """Enable/disable color controls based on mode selection."""
        self._update_color_controls(index == 1)

    def _update_color_controls(self, override_enabled: bool) -> None:
        """Enable or disable color picker controls.

        Args:
            override_enabled: True when override mode is selected.
        """
        self._color_btn.setEnabled(override_enabled)
        self._color_preview.setEnabled(override_enabled)
        self._color_hex.setEnabled(override_enabled)

    def _choose_color(self) -> None:
        """Open QColorDialog to select an override color."""
        color = QColorDialog.getColor(
            QColor(self._current_color),
            self,
            "Choose Annotation Color",
        )
        if color.isValid():
            self._current_color = color.name()
            self._color_preview.setStyleSheet(
                f"background-color: {self._current_color}; border: 1px solid gray;"
            )
            self._color_hex.setText(self._current_color)

    def get_selected_mode(self) -> str:
        """Get the currently selected color mode.

        Returns:
            "original" or "override".
        """
        if self._mode_combo.currentIndex() == 0:
            return "original"
        return "override"

    def get_selected_color(self) -> str:
        """Get the selected override color hex string.

        Returns:
            Hex color string like "#FF0000".
        """
        return self._current_color
