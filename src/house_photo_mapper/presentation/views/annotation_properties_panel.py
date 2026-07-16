"""AnnotationPropertiesPanel - Edit annotation metadata and color."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPixmap
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


class AnnotationPropertiesPanel(QWidget):
    """Panel for editing annotation metadata fields and color.

    Shows title, description, tags, and color inputs when an annotation is selected.
    Emits save_requested when the user clicks Save.
    """

    save_requested = Signal(str, str, str, str)  # annotation_id, title, description, tags_csv
    color_changed = Signal(str, str)  # annotation_id, hex_color
    link_photo_requested = Signal(str)  # annotation_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._annotation_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._title_label = QLabel("Annotation Properties")
        self._title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._title_label)

        form = QFormLayout()

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Title (required)")
        form.addRow("Title:", self._title_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Description")
        self._desc_edit.setMaximumHeight(80)
        form.addRow("Description:", self._desc_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("Comma-separated tags")
        form.addRow("Tags:", self._tags_edit)

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

        btn_layout = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._save_btn.setEnabled(False)
        btn_layout.addStretch()
        btn_layout.addWidget(self._save_btn)
        layout.addLayout(btn_layout)

        self._save_btn.clicked.connect(self._on_save)
        self._title_edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str) -> None:
        self._save_btn.setEnabled(bool(text.strip()) and self._annotation_id is not None)

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

    def _on_save(self) -> None:
        if self._annotation_id is None:
            return
        self.save_requested.emit(
            self._annotation_id,
            self._title_edit.text(),
            self._desc_edit.toPlainText(),
            self._tags_edit.text(),
        )

    def show_annotation(
        self, annotation_id: str, title: str, description: str, tags: list[str], color: str = "#DC2828",
        photo_path: str | None = None,
    ) -> None:
        """Populate fields for a selected annotation."""
        self._annotation_id = annotation_id
        self._title_edit.setText(title)
        self._desc_edit.setPlainText(description)
        self._tags_edit.setText(", ".join(tags))
        self._color_btn.set_color(color)
        self.set_photo_thumbnail(photo_path)
        self._save_btn.setEnabled(bool(title.strip()))
        self.setVisible(True)

    def clear(self) -> None:
        """Clear the panel."""
        self._annotation_id = None
        self._title_edit.clear()
        self._desc_edit.clear()
        self._tags_edit.clear()
        self._color_btn.set_color("#DC2828")
        self.set_photo_thumbnail(None)
        self._save_btn.setEnabled(False)
        self.setVisible(False)
