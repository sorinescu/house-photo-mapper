"""ProjectViewModel - Orchestrates project CRUD operations and emits state signals."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from house_photo_mapper.domain.models.plan import PlanModel
from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel

if TYPE_CHECKING:
    from house_photo_mapper.domain.services.persistence import PersistenceService
    from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel


class ProjectViewModel(QtSafeViewModel):
    """ViewModel for project management operations.

    Exposes slots for create/open/save/save-as operations. Emits signals
    for UI to react to project state changes. No UI logic - pure orchestration.
    """

    project_changed = Signal(object)  # emits ProjectModel or None
    dirty_changed = Signal(bool)
    error_occurred = Signal(str)
    recent_projects_changed = Signal(list)

    def __init__(
        self,
        persistence: "PersistenceService",
        parent: QObject | None = None,
    ) -> None:
        """Initialize ProjectViewModel.

        Args:
            persistence: PersistenceService instance for file I/O.
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._persistence = persistence
        self._project: ProjectModel | None = None
        self._dirty = False
        self._plan_vm: PlanViewModel | None = None
        self._plan_model: PlanModel | None = None

    @property
    def project(self) -> ProjectModel | None:
        """Return current project or None if no project loaded."""
        return self._project

    @property
    def dirty(self) -> bool:
        """Return True if current project has unsaved changes."""
        return self._dirty

    def _emit_project_changed(self) -> None:
        """Emit project_changed signal with current project."""
        self.project_changed.emit(self._project)

    def _emit_dirty_changed(self) -> None:
        """Emit dirty_changed signal with current dirty state."""
        self.dirty_changed.emit(self._dirty)

    def _emit_recent_projects_changed(self) -> None:
        """Emit recent_projects_changed signal."""
        self.recent_projects_changed.emit(self._persistence.get_recent_projects())

    @Slot(str)
    def new_project(self, path: str) -> None:
        """Create a new empty project at the given path.

        Args:
            path: File path for the new project.
        """
        try:
            project_path = Path(path)
            project_path.parent.mkdir(parents=True, exist_ok=True)

            self._project = ProjectModel.create_empty(project_path)
            self._dirty = True
            self._emit_project_changed()
            self._emit_dirty_changed()
        except Exception as e:
            self.error_occurred.emit(f"Failed to create project: {e}")

    @Slot(str)
    def open_project(self, path: str) -> None:
        """Open an existing project from the given path.

        Loads both .hpmpj and plans.json. Injects PlanModel into PlanViewModel.

        Args:
            path: File path to the .hpmpj project file.
        """
        try:
            self._project = self._persistence.load_project(path)
            self._dirty = False

            # Load PlanModel from plans.json
            project_dir = Path(path).parent
            self._plan_model = self._persistence.load_plan_model(project_dir)
            if self._plan_model is None:
                self._plan_model = PlanModel()

            # Inject into PlanViewModel if available
            if self._plan_vm is not None:
                self._plan_vm.plan_model = self._plan_model

            self._emit_project_changed()
            self._emit_dirty_changed()
            self._emit_recent_projects_changed()
        except Exception as e:
            self.error_occurred.emit(f"Failed to open project: {e}")

    @Slot()
    def save_project(self) -> None:
        """Save the current project to its existing path."""
        if self._project is None:
            self.error_occurred.emit("No project to save")
            return

        if not self._project.path:
            self.error_occurred.emit("Project has no path; use Save As")
            return

        try:
            self._persistence.save_project(self._project)
            # Save PlanModel if available
            project_dir = self._project_dir()
            if project_dir and self._plan_model is not None:
                self._persistence.save_plan_model(self._plan_model, project_dir)
            self._dirty = False
            self._emit_dirty_changed()
        except Exception as e:
            self.error_occurred.emit(f"Failed to save project: {e}")

    @Slot(str)
    def save_project_as(self, path: str) -> None:
        """Save the current project to a new path.

        Args:
            path: New file path for the project.
        """
        if self._project is None:
            self.error_occurred.emit("No project to save")
            return

        try:
            self._persistence.save_project_as(self._project, path)
            self._dirty = False
            self._emit_project_changed()
            self._emit_dirty_changed()
            self._emit_recent_projects_changed()
        except Exception as e:
            self.error_occurred.emit(f"Failed to save project as: {e}")

    @Slot()
    def close_project(self) -> None:
        """Close the current project without saving."""
        self._project = None
        self._dirty = False
        self._emit_project_changed()
        self._emit_dirty_changed()

    def mark_dirty(self) -> None:
        """Mark the current project as having unsaved changes."""
        if not self._dirty:
            self._dirty = True
            self._emit_dirty_changed()

    def get_recent_projects(self) -> list[str]:
        """Get list of recent project paths."""
        return self._persistence.get_recent_projects()

    def set_plan_vm(self, plan_vm: "PlanViewModel") -> None:
        """Set the PlanViewModel reference for plan persistence coordination.

        Args:
            plan_vm: PlanViewModel instance to coordinate with.
        """
        self._plan_vm = plan_vm

    @property
    def plan_model(self) -> PlanModel | None:
        """Get current PlanModel."""
        return self._plan_model

    def _project_dir(self) -> Path | None:
        """Get project directory from current project path."""
        if self._project and self._project.path:
            return Path(self._project.path).parent
        return None
