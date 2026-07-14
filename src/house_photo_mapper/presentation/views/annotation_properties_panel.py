"""AnnotationPropertiesPanel - Edit annotation metadata (title, description, tags)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AnnotationPropertiesPanel(QWidget):
    """Panel for editing annotation metadata fields.

    Shows title, description, and tags inputs when an annotation is selected.
    Emits save_requested when the user clicks Save.
    """

    save_requested = Signal(str, str, str, str)  # annotation_id, title, description, tags_csv

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

        layout.addLayout(form)

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

    def _on_save(self) -> None:
        if self._annotation_id is None:
            return
        self.save_requested.emit(
            self._annotation_id,
            self._title_edit.text(),
            self._desc_edit.toPlainText(),
            self._tags_edit.text(),
        )

    def show_annotation(self, annotation_id: str, title: str, description: str, tags: list[str]) -> None:
        """Populate fields for a selected annotation."""
        self._annotation_id = annotation_id
        self._title_edit.setText(title)
        self._desc_edit.setPlainText(description)
        self._tags_edit.setText(", ".join(tags))
        self._save_btn.setEnabled(bool(title.strip()))
        self.setVisible(True)

    def clear(self) -> None:
        """Clear the panel."""
        self._annotation_id = None
        self._title_edit.clear()
        self._desc_edit.clear()
        self._tags_edit.clear()
        self._save_btn.setEnabled(False)
        self.setVisible(False)
