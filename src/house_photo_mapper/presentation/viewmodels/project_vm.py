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
    from house_photo_mapper.presentation.viewmodels.photo_vm import PhotoViewModel
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
    photos_cleared = Signal()  # emitted when photos are cleared (new project)
    plan_cleared = Signal()  # emitted when plan is cleared (new project)

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
        self._photo_vm: PhotoViewModel | None = None
        self._annotation_vm = None

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

            # Clear photos and plan for new project
            if self._photo_vm is not None:
                self._photo_vm._photos.clear()
                self._photo_vm._thumbnail_generator.clear()
                self._photo_vm.photos_changed.emit()
                self.photos_cleared.emit()
            if self._plan_vm is not None:
                self._plan_vm.plan_model = PlanModel()
                self.plan_cleared.emit()

            self._emit_project_changed()
            self._emit_dirty_changed()
        except Exception as e:
            self.error_occurred.emit(f"Failed to create project: {e}")

    @Slot(str)
    def open_project(self, path: str) -> None:
        """Open an existing project from the given path.

        Loads both .hpmpj, plans.json, and photos.json. Injects PlanModel
        into PlanViewModel and populates PhotoViewModel.

        Args:
            path: File path to the .hpmpj project file.
        """
        try:
            self._project = self._persistence.load_project(path)
            self._dirty = False

            project_dir = Path(path).parent

            # Load PlanModel from plans.json
            self._plan_model = self._persistence.load_plan_model(project_dir)
            if self._plan_model is None:
                self._plan_model = PlanModel()

            # Inject into PlanViewModel if available
            if self._plan_vm is not None:
                self._plan_vm.plan_model = self._plan_model

            # Load photos from photos.json
            if self._photo_vm is not None:
                photos = self._persistence.load_photo_model(project_dir)
                if photos:
                    # Populate PhotoViewModel and emit signals for each photo
                    for photo in photos:
                        self._photo_vm._photos.append(photo)
                        self._photo_vm.photo_added.emit(photo)
                        # Generate thumbnail using original_path if available, otherwise compute full_path
                        if photo.original_path:
                            full_path = photo.original_path
                        else:
                            full_path = str(project_dir / photo.path)
                        self._photo_vm._thumbnail_generator.generate(photo.path, full_path)

            # Load annotations from ProjectModel
            if self._annotation_vm is not None and self._project.annotations:
                from house_photo_mapper.domain.models.annotation import AnnotationModel
                for ann_data in self._project.annotations:
                    ann = AnnotationModel.from_project_json(ann_data)
                    self._annotation_vm._annotations[ann.annotation_id] = ann
                self._annotation_vm.annotations_changed.emit(
                    [a.annotation_id for a in self._annotation_vm.get_all_annotations()]
                )

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
            # Serialize annotations from AnnotationViewModel into ProjectModel
            if self._annotation_vm is not None:
                self._project.annotations = [
                    ann.to_project_json()
                    for ann in self._annotation_vm.get_all_annotations()
                ]

            self._persistence.save_project(self._project)
            project_dir = self._project_dir()

            # Save PlanModel if available
            if project_dir and self._plan_model is not None:
                self._persistence.save_plan_model(self._plan_model, project_dir)

            # Save photos if available
            if project_dir and self._photo_vm is not None:
                self._persistence.save_photo_model(self._photo_vm.photos, project_dir)

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
            # Serialize annotations from AnnotationViewModel into ProjectModel
            if self._annotation_vm is not None:
                self._project.annotations = [
                    ann.to_project_json()
                    for ann in self._annotation_vm.get_all_annotations()
                ]

            self._persistence.save_project_as(self._project, path)
            project_dir = Path(path).parent

            # Save PlanModel if available
            if self._plan_model is not None:
                self._persistence.save_plan_model(self._plan_model, project_dir)

            # Save photos if available
            if self._photo_vm is not None:
                self._persistence.save_photo_model(self._photo_vm.photos, project_dir)

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

    def set_annotation_vm(self, annotation_vm) -> None:
        """Set the AnnotationViewModel reference for persistence coordination.

        Args:
            annotation_vm: AnnotationViewModel instance.
        """
        self._annotation_vm = annotation_vm

    def set_photo_vm(self, photo_vm: "PhotoViewModel") -> None:
        """Set the PhotoViewModel reference for photo persistence coordination.

        Args:
            photo_vm: PhotoViewModel instance to coordinate with.
        """
        self._photo_vm = photo_vm

    @property
    def plan_vm(self) -> "PlanViewModel | None":
        """Return the PlanViewModel instance (if set)."""
        return self._plan_vm

    @property
    def photo_vm(self) -> "PhotoViewModel | None":
        """Return the PhotoViewModel instance (if set)."""
        return self._photo_vm

    @property
    def plan_model(self) -> PlanModel | None:
        """Get current PlanModel."""
        return self._plan_model

    def _project_dir(self) -> Path | None:
        """Get project directory from current project path."""
        if self._project and self._project.path:
            return Path(self._project.path).parent
        return None
