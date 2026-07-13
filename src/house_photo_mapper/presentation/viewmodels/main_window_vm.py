"""MainWindowViewModel - Composes ProjectViewModel and handles window-level actions."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel
from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel

if TYPE_CHECKING:
    pass


class MainWindowViewModel(QtSafeViewModel):
    """Main window ViewModel - composes ProjectViewModel and handles file dialogs.

    This ViewModel owns the ProjectViewModel and delegates project operations to it.
    It handles file dialog interactions (New, Open, Save As) which require UI context.
    """

    project_vm_changed = Signal(object)  # emits ProjectViewModel
    window_title_changed = Signal(str)
    status_message_changed = Signal(str)
    recent_projects_changed = Signal(list)

    def __init__(
        self,
        persistence: "PersistenceService",
        parent: QObject | None = None,
    ) -> None:
        """Initialize MainWindowViewModel.

        Args:
            persistence: PersistenceService for file I/O and settings.
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._persistence = persistence
        self._project_vm = ProjectViewModel(persistence, parent=self)

        # Forward signals from ProjectViewModel
        self._project_vm.project_changed.connect(self._on_project_changed)
        self._project_vm.dirty_changed.connect(self._on_dirty_changed)
        self._project_vm.error_occurred.connect(self._on_error)
        self._project_vm.recent_projects_changed.connect(
            self.recent_projects_changed.emit
        )

    @property
    def project_vm(self) -> ProjectViewModel:
        """Return the ProjectViewModel instance."""
        return self._project_vm

    @property
    def project(self) -> ProjectModel | None:
        """Return current ProjectModel or None."""
        return self._project_vm.project

    @property
    def dirty(self) -> bool:
        """Return True if current project has unsaved changes."""
        return self._project_vm.dirty

    def _on_project_changed(self, project: ProjectModel | None) -> None:
        """Handle project change from ProjectViewModel."""
        self.project_vm_changed.emit(self._project_vm)
        self._update_window_title()

    def _on_dirty_changed(self, dirty: bool) -> None:
        """Handle dirty state change."""
        self._update_window_title()

    def _on_error(self, message: str) -> None:
        """Handle error from ProjectViewModel."""
        self.status_message_changed.emit(f"Error: {message}")

    def _update_window_title(self) -> None:
        """Update window title based on current project and dirty state."""
        if self._project_vm.project is None:
            title = "HousePhotoMapper"
        else:
            name = self._project_vm.project.project_name
            dirty_mark = " *" if self._project_vm.dirty else ""
            title = f"{name}{dirty_mark} — HousePhotoMapper"
        self.window_title_changed.emit(title)

    @Slot()
    def new_project(self) -> None:
        """Show New Project dialog and create project."""
        directory = self._persistence.get_last_opened_directory()
        path, _ = QFileDialog.getSaveFileName(
            None,  # parent widget will be set by view
            "New Project",
            str(Path(directory) / "Untitled.hpmpj"),
            "HousePhotoMapper Projects (*.hpmpj)",
        )
        if path:
            self._persistence.set_last_opened_directory(str(Path(path).parent))
            self._project_vm.new_project(path)

    @Slot()
    def open_project(self) -> None:
        """Show Open Project dialog and load project."""
        directory = self._persistence.get_last_opened_directory()
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Open Project",
            directory,
            "HousePhotoMapper Projects (*.hpmpj)",
        )
        if path:
            self._persistence.set_last_opened_directory(str(Path(path).parent))
            self._project_vm.open_project(path)

    @Slot()
    def save_project(self) -> None:
        """Save current project to its existing path."""
        if self._project_vm.project is None:
            self.status_message_changed.emit("No project to save")
            return

        if not self._project_vm.project.path:
            self.save_project_as()
            return

        self._project_vm.save_project()

    @Slot()
    def save_project_as(self) -> None:
        """Show Save As dialog and save project to new path."""
        if self._project_vm.project is None:
            self.status_message_changed.emit("No project to save")
            return

        directory = self._persistence.get_last_opened_directory()
        default_name = self._project_vm.project.project_name + ".hpmpj"
        path, _ = QFileDialog.getSaveFileName(
            None,
            "Save Project As",
            str(Path(directory) / default_name),
            "HousePhotoMapper Projects (*.hpmpj)",
        )
        if path:
            self._persistence.set_last_opened_directory(str(Path(path).parent))
            self._project_vm.save_project_as(path)

    @Slot(str)
    def open_recent_project(self, path: str) -> None:
        """Open a project from the recent projects list.

        Args:
            path: Path to the project file.
        """
        if path:
            self._project_vm.open_project(path)

    def get_recent_projects(self) -> list[str]:
        """Get list of recent project paths."""
        return self._project_vm.get_recent_projects()

    def restore_window_geometry(self, window: QMainWindow) -> None:
        """Restore window geometry and state from settings.

        Args:
            window: QMainWindow instance to restore.
        """
        geometry = self._persistence.load_window_geometry()
        if geometry:
            window.restoreGeometry(geometry)

        state = self._persistence.load_window_state()
        if state:
            window.restoreState(state)

    def save_window_geometry(self, window: QMainWindow) -> None:
        """Save window geometry and state to settings.

        Args:
            window: QMainWindow instance to save.
        """
        self._persistence.save_window_geometry(bytes(window.saveGeometry().data()))
        self._persistence.save_window_state(bytes(window.saveState().data()))

    def maybe_save_before_close(self, window: QMainWindow) -> bool:
        """Prompt to save if project is dirty before closing.

        Args:
            window: Parent widget for dialog.

        Returns:
            True if close should proceed, False if cancelled.
        """
        if not self._project_vm.dirty:
            return True

        reply = QMessageBox.question(
            window,
            "Unsaved Changes",
            "The project has unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            if self._project_vm.project and not self._project_vm.project.path:
                self.save_project_as()
                return not self._project_vm.dirty
            else:
                self.save_project()
                return not self._project_vm.dirty
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False
