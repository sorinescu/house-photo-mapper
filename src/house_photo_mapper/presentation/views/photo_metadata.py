"""PhotoMetadataPanel - Widget for displaying photo EXIF metadata."""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PhotoMetadataPanel(QWidget):
    """Panel for displaying photo metadata.

    Shows filename, dimensions, file size, timestamp, camera, lens,
    and GPS coordinates in a form layout.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize PhotoMetadataPanel.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Group box
        group = QGroupBox("Photo Metadata")
        group_layout = QFormLayout(group)

        # Labels for metadata fields
        self._filename_label = QLabel("No photo selected")
        self._dimensions_label = QLabel("")
        self._size_label = QLabel("")
        self._camera_label = QLabel("")
        self._lens_label = QLabel("")
        self._date_label = QLabel("")
        self._gps_label = QLabel("")

        # Add rows
        group_layout.addRow("Filename:", self._filename_label)
        group_layout.addRow("Dimensions:", self._dimensions_label)
        group_layout.addRow("Size:", self._size_label)
        group_layout.addRow("Camera:", self._camera_label)
        group_layout.addRow("Lens:", self._lens_label)
        group_layout.addRow("Date:", self._date_label)
        group_layout.addRow("GPS:", self._gps_label)

        layout.addWidget(group)
        layout.addStretch()

    @Slot(dict)
    def update_metadata(self, metadata: dict) -> None:
        """Update displayed metadata.

        Args:
            metadata: Dictionary with metadata fields.
        """
        if not metadata:
            self._filename_label.setText("No photo selected")
            self._dimensions_label.setText("")
            self._size_label.setText("")
            self._camera_label.setText("")
            self._lens_label.setText("")
            self._date_label.setText("")
            self._gps_label.setText("")
            return

        self._filename_label.setText(metadata.get("Filename", ""))
        self._dimensions_label.setText(metadata.get("Dimensions", ""))
        self._size_label.setText(metadata.get("Size", ""))
        self._camera_label.setText(metadata.get("Camera", ""))
        self._lens_label.setText(metadata.get("Lens", ""))
        self._date_label.setText(metadata.get("Date", ""))
        self._gps_label.setText(metadata.get("GPS", ""))

    def clear(self) -> None:
        """Clear all displayed metadata."""
        self.update_metadata({})
