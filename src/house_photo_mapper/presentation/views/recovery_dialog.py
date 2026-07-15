"""RecoveryDialog - Shows recoverable projects after a crash.

Displays a list of .bak files found by RecoveryScanner, allowing the user
to select which project to recover, preview project data, and dismiss.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from house_photo_mapper.infrastructure.recovery import RecoverableProject

logger = logging.getLogger(__name__)


class RecoveryDialog(QDialog):
    """Dialog for selecting and recovering projects from .bak files.

    Displays a table of recoverable projects with timestamps and preview data.
    Allows the user to select one or more projects to recover, or dismiss.

    Signals:
        recovery_selected: Emitted with list of bak_path objects to recover.
    """

    recovery_selected = Signal(list)  # list[Path]

    def __init__(
        self,
        recoverable_projects: list[RecoverableProject],
        parent: QWidget | None = None,
    ) -> None:
        """Initialize RecoveryDialog.

        Args:
            recoverable_projects: List of RecoverableProject instances to show.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._projects = recoverable_projects
        self._selected_indices: list[int] = []

        self.setWindowTitle("Crash Recovery")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self) -> None:
        """Set up the dialog layout."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            f"Found {len(self._projects)} recoverable project(s):"
        )
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        description = QLabel(
            "These projects were saved recently before the application closed. "
            "Select one or more to recover, or dismiss to start fresh."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Project table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Project",
            "Modified",
            "Photos",
            "Annotations",
            "Plans",
        ])
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Buttons
        button_layout = QHBoxLayout()

        self._recover_btn = QPushButton("Recover Selected")
        self._recover_btn.setEnabled(False)
        self._recover_btn.clicked.connect(self._on_recover)
        button_layout.addWidget(self._recover_btn)

        self._recover_all_btn = QPushButton("Recover All")
        self._recover_all_btn.clicked.connect(self._on_recover_all)
        button_layout.addWidget(self._recover_all_btn)

        button_layout.addStretch()

        self._dismiss_btn = QPushButton("Dismiss")
        self._dismiss_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._dismiss_btn)

        layout.addLayout(button_layout)

    def _populate_table(self) -> None:
        """Populate the table with recoverable projects."""
        self._table.setRowCount(len(self._projects))

        for row, project in enumerate(self._projects):
            # Project name
            name_item = QTableWidgetItem(project.project_name)
            name_item.setData(Qt.ItemDataRole.UserRole, project)
            self._table.setItem(row, 0, name_item)

            # Modified time
            modified_str = project.modified_at.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            self._table.setItem(row, 1, QTableWidgetItem(modified_str))

            # Photo count
            self._table.setItem(
                row, 2, QTableWidgetItem(str(project.photo_count))
            )

            # Annotation count
            self._table.setItem(
                row, 3, QTableWidgetItem(str(project.annotation_count))
            )

            # Plan count
            self._table.setItem(
                row, 4, QTableWidgetItem(str(project.plan_count))
            )

    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._table.selectedItems()
        # Only enable if at least one row is selected
        has_selection = len(selected) > 0
        self._recover_btn.setEnabled(has_selection)

    @Slot()
    def _on_recover(self) -> None:
        """Handle Recover Selected button click."""
        selected_rows = set()
        for item in self._table.selectedItems():
            selected_rows.add(item.row())

        bak_paths = []
        for row in sorted(selected_rows):
            item = self._table.item(row, 0)
            if item:
                project = item.data(Qt.ItemDataRole.UserRole)
                if project:
                    bak_paths.append(project.bak_path)

        if bak_paths:
            self.recovery_selected.emit(bak_paths)
            self.accept()

    @Slot()
    def _on_recover_all(self) -> None:
        """Handle Recover All button click."""
        bak_paths = [p.bak_path for p in self._projects]
        if bak_paths:
            self.recovery_selected.emit(bak_paths)
            self.accept()
