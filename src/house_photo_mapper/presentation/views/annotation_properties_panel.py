"""AnnotationPropertiesPanel - Edit annotation metadata and color."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ColorButton(QPushButton):
    """Button that shows current color and opens color picker on click."""

    color_changed = Signal(str)  # hex color string

    def __init__(self, color: str = "#DC2828", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 24)
        self.setCursor(self.cursor())
        self.clicked.connect(self._pick_color)
        self._update_style()

    def _update_style(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #888; border-radius: 3px;"
        )

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, "Annotation Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._update_style()


class _TabFilterTextEdit(QTextEdit):
    """QTextEdit that intercepts Tab to move focus instead of inserting a tab char."""

    def event(self, event: QEvent) -> bool:
        if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.focusNextChild()
                return True
        return super().event(event)


class AnnotationPropertiesPanel(QWidget):
    """Panel for editing annotation metadata fields and color.

    Shows title, description, and color inputs when an annotation is selected.
    Changes are emitted immediately via metadata_changed signal.
    """

    metadata_changed = Signal(str, str, str)  # annotation_id, title, description
    color_changed = Signal(str, str)  # annotation_id, hex_color
    link_photo_requested = Signal(str)  # annotation_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._annotation_id: str | None = None
        self._block_signals = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._title_label = QLabel("Annotation Properties")
        self._title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._title_label)

        form = QFormLayout()

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Title (required)")
        self._title_edit.textChanged.connect(self._on_title_changed)
        form.addRow("Title:", self._title_edit)

        self._desc_edit = _TabFilterTextEdit()
        self._desc_edit.setPlaceholderText("Description")
        self._desc_edit.setMaximumHeight(80)
        self._desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self._desc_edit)

        self._color_btn = ColorButton()
        self._color_btn.color_changed.connect(self._on_color_changed)
        form.addRow("Color:", self._color_btn)

        layout.addLayout(form)

        # Photo section
        photo_layout = QHBoxLayout()

        self._photo_thumbnail = QLabel()
        self._photo_thumbnail.setFixedSize(60, 60)
        self._photo_thumbnail.setStyleSheet("border: 1px solid #888; background-color: #f0f0f0;")
        self._photo_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_layout.addWidget(self._photo_thumbnail)

        photo_btn_layout = QVBoxLayout()
        self._photo_label = QLabel("No photo linked")
        self._photo_label.setStyleSheet("color: #888;")
        photo_btn_layout.addWidget(self._photo_label)

        self._link_photo_btn = QPushButton("Link Photo")
        self._link_photo_btn.setEnabled(False)
        self._link_photo_btn.clicked.connect(self._on_link_photo)
        photo_btn_layout.addWidget(self._link_photo_btn)

        photo_layout.addLayout(photo_btn_layout)
        photo_layout.addStretch()
        layout.addLayout(photo_layout)

    def _on_title_changed(self, text: str) -> None:
        if self._block_signals or self._annotation_id is None:
            return
        if text.strip():
            self.metadata_changed.emit(
                self._annotation_id,
                self._title_edit.text(),
                self._desc_edit.toPlainText(),
            )

    def _on_desc_changed(self) -> None:
        if self._block_signals or self._annotation_id is None:
            return
        if self._title_edit.text().strip():
            self.metadata_changed.emit(
                self._annotation_id,
                self._title_edit.text(),
                self._desc_edit.toPlainText(),
            )

    def _on_link_photo(self) -> None:
        if self._annotation_id is not None:
            self.link_photo_requested.emit(self._annotation_id)

    def set_photo_thumbnail(self, photo_path: str | None) -> None:
        """Set the photo thumbnail from a file path."""
        if photo_path and Path(photo_path).is_file():
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._photo_thumbnail.setPixmap(scaled)
                self._photo_label.setText(Path(photo_path).name)
                self._photo_label.setStyleSheet("")
                return
        self._photo_thumbnail.clear()
        self._photo_label.setText("No photo linked")
        self._photo_label.setStyleSheet("color: #888;")

    def set_link_photo_enabled(self, enabled: bool) -> None:
        """Enable/disable the Link Photo button."""
        self._link_photo_btn.setEnabled(enabled)

    def _on_color_changed(self, color: str) -> None:
        if self._annotation_id is not None:
            self.color_changed.emit(self._annotation_id, color)

    def show_annotation(
        self, annotation_id: str, title: str, description: str, color: str = "#DC2828",
        photo_path: str | None = None,
    ) -> None:
        """Populate fields for a selected annotation."""
        self._block_signals = True
        self._annotation_id = annotation_id
        self._title_edit.setText(title)
        self._desc_edit.setPlainText(description)
        self._color_btn.set_color(color)
        self.set_photo_thumbnail(photo_path)
        self._block_signals = False
        self.setVisible(True)

    def clear(self) -> None:
        """Clear the panel."""
        self._block_signals = True
        self._annotation_id = None
        self._title_edit.clear()
        self._desc_edit.clear()
        self._color_btn.set_color("#DC2828")
        self.set_photo_thumbnail(None)
        self._block_signals = False
        self.setVisible(False)
