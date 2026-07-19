"""ReportConfigDialog — Combined report generation settings (layout + annotation colors).

Single dialog for configuring page format, orientation, and annotation color
preferences before generating a PDF report. Settings persist via QSettings.
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


class ReportConfigDialog(QDialog):
    """Dialog for report generation settings: layout and annotation colors.

    Provides:
    - Page format (A4, US Letter) and orientation (Portrait, Landscape)
    - Annotation color mode (original or override) with color picker

    Returns dialog result (Accepted/Rejected) and accessor methods for
    reading all selections.
    """

    def __init__(
        self,
        current_format: str = "A4",
        current_orientation: str = "Portrait",
        current_color_mode: str = "original",
        current_color: str = "#DC2828",
        parent=None,
    ) -> None:
        """Initialize ReportConfigDialog.

        Args:
            current_format: Initial page format ("A4" or "US Letter").
            current_orientation: Initial orientation ("Portrait" or "Landscape").
            current_color_mode: Initial color mode ("original" or "override").
            current_color: Initial override color hex string.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Generate Report")
        self.setMinimumSize(380, 320)

        self._current_color = current_color

        self._setup_ui(current_format, current_orientation, current_color_mode)
        self._connect_signals()

        self._update_color_controls(current_color_mode == "override")

    def _setup_ui(
        self,
        current_format: str,
        current_orientation: str,
        current_color_mode: str,
    ) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # --- Page Format group ---
        format_group = QGroupBox("Page Format")
        format_form = QFormLayout()

        self._format_combo = QComboBox()
        self._format_combo.setObjectName("format_combo")
        self._format_combo.addItems(["A4", "US Letter"])
        idx = self._format_combo.findText(current_format)
        if idx >= 0:
            self._format_combo.setCurrentIndex(idx)
        format_form.addRow("Format:", self._format_combo)

        self._orientation_combo = QComboBox()
        self._orientation_combo.setObjectName("orientation_combo")
        self._orientation_combo.addItems(["Portrait", "Landscape"])
        idx = self._orientation_combo.findText(current_orientation)
        if idx >= 0:
            self._orientation_combo.setCurrentIndex(idx)
        format_form.addRow("Orientation:", self._orientation_combo)

        format_group.setLayout(format_form)
        layout.addWidget(format_group)

        # --- Annotation Colors group ---
        color_group = QGroupBox("Annotation Colors")
        color_form = QFormLayout()

        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("mode_combo")
        self._mode_combo.addItems(["Use original colors", "Override with custom color"])
        if current_color_mode == "override":
            self._mode_combo.setCurrentIndex(1)
        color_form.addRow("Colors:", self._mode_combo)

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
        color_row.addWidget(self._color_btn)

        color_form.addRow("Override:", color_row)

        color_group.setLayout(color_form)
        layout.addWidget(color_group)

        # --- Buttons ---
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
        """Connect button and combo signals."""
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._color_btn.clicked.connect(self._choose_color)

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

    # --- Accessors ---

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

    def get_selected_color_mode(self) -> str:
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
