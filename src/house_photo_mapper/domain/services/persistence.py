"""PersistenceService - Handles JSON file I/O and QSettings for window state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings

from house_photo_mapper.domain.models.project import ProjectModel


class PersistenceService:
    """Service for persisting projects and application settings.

    Handles:
    - Project JSON serialization/deserialization (atomic writes)
    - Recent projects list via QSettings
    - Window geometry and state via QSettings
    - Last opened directory for file dialogs
    """

    def __init__(self) -> None:
        """Initialize PersistenceService with QSettings."""
        self._settings = QSettings(
            QSettings.Format.NativeFormat,
            QSettings.Scope.UserScope,
            "HousePhotoMapper",
            "HousePhotoMapper",
        )

    def save_project(self, project: ProjectModel) -> None:
        """Save project to its path atomically.

        Args:
            project: ProjectModel to save.

        Raises:
            ValueError: If project has no path set.
            OSError: If write fails.
        """
        if not project.path:
            raise ValueError("Cannot save project: no path set")

        path = Path(project.path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to .tmp then rename
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(project.model_dump_json(indent=2))
        tmp_path.replace(path)

        project.mark_clean()
        self._add_recent_project(str(path))

    def load_project(self, path: str) -> ProjectModel:
        """Load and validate project from file.

        Args:
            path: Path to .hpmpj project file.

        Returns:
            Validated ProjectModel instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValidationError: If JSON doesn't match schema.
        """
        data = Path(path).read_text()
        project = ProjectModel.model_validate_json(data)
        project.path = path
        project.mark_clean()
        self._add_recent_project(path)
        return project

    def save_project_as(self, project: ProjectModel, new_path: str) -> None:
        """Save project to a new path and update project's path.

        Args:
            project: ProjectModel to save.
            new_path: New file path.
        """
        project.path = new_path
        self.save_project(project)

    def get_recent_projects(self) -> list[str]:
        """Get list of recent project paths (max 10)."""
        value: Any = self._settings.value("recentProjects", [], type=list)
        return list(value) if value else []

    def get_last_opened_directory(self) -> str:
        """Get the last directory used for opening/saving projects."""
        value: Any = self._settings.value("lastOpenedDirectory", "", type=str)
        return value if value else ""

    def set_last_opened_directory(self, directory: str) -> None:
        """Set the last directory used for opening/saving projects.

        Args:
            directory: Directory path to store.
        """
        self._settings.setValue("lastOpenedDirectory", directory)

    def _add_recent_project(self, path: str) -> None:
        """Add project to recent list, deduplicate, limit to 10."""
        recent = self.get_recent_projects()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._settings.setValue("recentProjects", recent[:10])

    def save_window_geometry(self, geometry: bytes) -> None:
        """Save main window geometry."""
        self._settings.setValue("mainWindow/geometry", geometry)

    def load_window_geometry(self) -> bytes | None:
        """Load main window geometry."""
        value: Any = self._settings.value("mainWindow/geometry", type=bytes)
        return bytes(value) if value else None

    def save_window_state(self, state: bytes) -> None:
        """Save main window state (toolbars, dock widgets)."""
        self._settings.setValue("mainWindow/state", state)

    def load_window_state(self) -> bytes | None:
        """Load main window state."""
        value: Any = self._settings.value("mainWindow/state", type=bytes)
        return bytes(value) if value else None
