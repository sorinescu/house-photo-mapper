"""PersistenceService - Handles JSON file I/O, atomic writes, .bak files, and schema versioning."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings

from house_photo_mapper.domain.models.photo import PhotoModel
from house_photo_mapper.domain.models.plan import PlanModel
from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.models.project_schema import (
    SCHEMA_VERSION,
    migrate_schema,
    validate_schema_version,
)

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service for persisting projects and application settings.

    Handles:
    - Project JSON serialization/deserialization (atomic writes)
    - .bak file management (keeps previous save as backup)
    - Schema version checking on load with forward/backward compatibility
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
        """Save project to its path atomically with .bak backup.

        The save process:
        1. If the target file exists, copy it to .bak (previous save backup)
        2. Write JSON to .tmp file (atomic write staging)
        3. Rename .tmp to target (atomic on same filesystem)
        4. Mark project clean and update recent projects

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

        # Update timestamps
        now = datetime.now(timezone.utc).isoformat()
        project.ui_state.setdefault("_last_saved", now)

        # Create .bak backup of previous save
        if path.exists():
            bak_path = path.with_suffix(".hpmpj.bak")
            try:
                shutil.copy2(path, bak_path)
            except OSError:
                logger.warning("Failed to create .bak backup for %s", path)

        # Atomic write: write to .tmp then rename
        tmp_path = path.with_suffix(".tmp")
        try:
            tmp_path.write_text(project.model_dump_json(indent=2))
            tmp_path.replace(path)
        except OSError:
            # Clean up .tmp on failure
            tmp_path.unlink(missing_ok=True)
            raise

        project.mark_clean()
        self._add_recent_project(str(path))
        self.set_last_opened_project(str(path))

    def load_project(self, path: str) -> ProjectModel:
        """Load and validate project from file with schema version checking.

        The load process:
        1. Read JSON from file
        2. Validate schema_version is supported (not newer than current)
        3. Run any necessary schema migrations
        4. Deserialize into ProjectModel with Pydantic validation
        5. If schema_version is missing (legacy file), default to version 1

        Args:
            path: Path to .hpmpj project file.

        Returns:
            Validated ProjectModel instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If schema version is newer than supported.
            ValidationError: If JSON doesn't match schema.
        """
        raw_data = json.loads(Path(path).read_text())

        # Schema version check — handle both versioned and legacy files
        file_version = raw_data.get("schema_version", 1)
        validate_schema_version(file_version)

        # Run any necessary migrations
        if file_version < SCHEMA_VERSION:
            raw_data = migrate_schema(raw_data, file_version)
            logger.info(
                "Migrated project schema from v%d to v%d",
                file_version,
                SCHEMA_VERSION,
            )

        project = ProjectModel.model_validate(raw_data)
        project.path = path
        project.mark_clean()
        self._add_recent_project(path)
        self.set_last_opened_project(path)

        # Log data integrity warnings
        warnings = self._validate_project_data(project)
        if warnings:
            for warning in warnings:
                logger.warning("Data integrity: %s", warning)

        return project

    def load_project_from_backup(self, bak_path: str) -> ProjectModel:
        """Load project from .bak backup file.

        Args:
            bak_path: Path to the .hpmpj.bak backup file.

        Returns:
            Validated ProjectModel instance.

        Raises:
            FileNotFoundError: If backup file doesn't exist.
        """
        # Convert .bak path to main project path for ProjectModel.path
        main_path = bak_path.replace(".hpmpj.bak", ".hpmpj")
        raw_data = json.loads(Path(bak_path).read_text())

        file_version = raw_data.get("schema_version", 1)
        validate_schema_version(file_version)

        if file_version < SCHEMA_VERSION:
            raw_data = migrate_schema(raw_data, file_version)

        project = ProjectModel.model_validate(raw_data)
        project.path = main_path
        project.mark_clean()
        return project

    def recover_project(self, bak_path: str) -> ProjectModel:
        """Recover a project from a .bak backup file with validation and logging.

        Validates the recovered data, logs recovery operations, and returns
        a clean ProjectModel ready to be saved to a new location.

        Args:
            bak_path: Path to the .hpmpj.bak backup file.

        Returns:
            Validated ProjectModel instance with path set to original location.

        Raises:
            FileNotFoundError: If backup file doesn't exist.
            ValueError: If recovered data fails schema validation.
        """
        logger.info("Starting recovery from .bak: %s", bak_path)

        try:
            project = self.load_project_from_backup(bak_path)
        except Exception as e:
            logger.error("Recovery failed for %s: %s", bak_path, e)
            raise

        # Log recovery details
        photo_count = len(project.photos)
        annotation_count = len(project.annotations)
        plan_count = len(project.plans)
        logger.info(
            "Recovery successful: %d photos, %d annotations, %d plans",
            photo_count,
            annotation_count,
            plan_count,
        )

        # Validate annotation references
        warnings = self._validate_recovered_data(project)
        if warnings:
            for warning in warnings:
                logger.warning("Recovery validation warning: %s", warning)

        return project

    def _validate_recovered_data(self, project: ProjectModel) -> list[str]:
        """Validate recovered project data and return warnings.

        Args:
            project: ProjectModel to validate.

        Returns:
            List of warning messages for data inconsistencies.
        """
        return self._validate_project_data(project)

    def _validate_project_data(self, project: ProjectModel) -> list[str]:
        """Validate project data integrity and return warnings.

        Checks:
        - JSON structure (required fields present)
        - Annotation references (photo_path exists in photos list)
        - Photo data completeness (path field present)
        - Annotation data completeness (required fields present)

        Args:
            project: ProjectModel to validate.

        Returns:
            List of warning messages for data inconsistencies.
        """
        warnings: list[str] = []

        # Check JSON structure - basic field presence
        if not hasattr(project, "schema_version"):
            warnings.append("Missing schema_version field")

        # Build photo path index for reference validation
        photo_paths = {p.get("path", "") for p in project.photos}

        # Validate annotation references
        for i, annotation in enumerate(project.annotations):
            photo_path = annotation.get("photo_path", "")
            if photo_path and photo_path not in photo_paths:
                warnings.append(
                    f"Annotation {i} references missing photo: {photo_path}"
                )

        # Check for required fields in photos
        for i, photo in enumerate(project.photos):
            if not photo.get("path"):
                warnings.append(f"Photo {i} missing path field")

        # Check for required fields in annotations
        for i, annotation in enumerate(project.annotations):
            if not annotation.get("annotation_id"):
                warnings.append(f"Annotation {i} missing annotation_id field")
            if "position_x" not in annotation or "position_y" not in annotation:
                warnings.append(f"Annotation {i} missing position field")

        return warnings

    def save_project_as(self, project: ProjectModel, new_path: str) -> None:
        """Save project to a new path and update project's path.

        Args:
            project: ProjectModel to save.
            new_path: New file path.
        """
        project.path = new_path
        self.save_project(project)

    def save_plan_model(self, plan: PlanModel, project_dir: Path) -> None:
        """Save PlanModel to project_dir/plans.json atomically.

        Args:
            plan: PlanModel to save.
            project_dir: Project directory containing plans.json.

        Raises:
            OSError: If write fails.
        """
        plan_path = project_dir / "plans.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to .tmp then rename
        tmp_path = plan_path.with_suffix(".tmp")
        tmp_path.write_text(plan.model_dump_json(indent=2))
        tmp_path.replace(plan_path)

    def load_plan_model(self, project_dir: Path) -> PlanModel | None:
        """Load PlanModel from project_dir/plans.json.

        Args:
            project_dir: Project directory containing plans.json.

        Returns:
            Validated PlanModel instance, or None if file doesn't exist.

        Raises:
            ValidationError: If JSON doesn't match PlanModel schema.
        """
        plan_path = project_dir / "plans.json"
        if not plan_path.exists():
            return None
        return PlanModel.model_validate_json(plan_path.read_text())

    def save_photo_model(self, photos: list[PhotoModel], project_dir: Path) -> None:
        """Save photo list to project_dir/photos.json atomically.

        Args:
            photos: List of PhotoModel instances to save.
            project_dir: Project directory containing photos.json.

        Raises:
            OSError: If write fails.
        """
        photos_path = project_dir / "photos.json"
        photos_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-compatible dicts
        photos_data = [photo.to_project_json() for photo in photos]

        # Atomic write: write to .tmp then rename
        tmp_path = photos_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(photos_data, indent=2))
        tmp_path.replace(photos_path)

    def load_photo_model(self, project_dir: Path) -> list[PhotoModel] | None:
        """Load photo list from project_dir/photos.json.

        Args:
            project_dir: Project directory containing photos.json.

        Returns:
            List of PhotoModel instances, or None if file doesn't exist.

        Raises:
            ValidationError: If JSON doesn't match PhotoModel schema.
        """
        photos_path = project_dir / "photos.json"
        if not photos_path.exists():
            return None

        photos_data = json.loads(photos_path.read_text())
        return [PhotoModel.from_project_json(data) for data in photos_data]

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

    def get_auto_save_enabled(self) -> bool:
        """Get whether auto-save is enabled (default: True)."""
        value: Any = self._settings.value("autoSave/enabled", True, type=bool)
        return bool(value)

    def set_auto_save_enabled(self, enabled: bool) -> None:
        """Set whether auto-save is enabled.

        Args:
            enabled: True to enable auto-save, False to disable.
        """
        self._settings.setValue("autoSave/enabled", enabled)

    def get_auto_save_interval(self) -> int:
        """Get auto-save interval in seconds (default: 120 = 2 minutes)."""
        value: Any = self._settings.value("autoSave/intervalSeconds", 120, type=int)
        return int(value) if value else 120

    def set_auto_save_interval(self, seconds: int) -> None:
        """Set auto-save interval in seconds.

        Args:
            seconds: Interval in seconds (minimum 5).
        """
        self._settings.setValue("autoSave/intervalSeconds", max(5, seconds))

    def get_last_opened_project(self) -> str | None:
        """Get the path of the last opened project, or None."""
        value: Any = self._settings.value("lastOpenedProject", "", type=str)
        logger.debug("get_last_opened_project: raw=%r, result=%r", value, value if value else None)
        return value if value else None

    def set_last_opened_project(self, path: str) -> None:
        """Store the path of the last opened project.

        Args:
            path: Absolute path to the project file.
        """
        logger.debug("set_last_opened_project: %s", path)
        self._settings.setValue("lastOpenedProject", path)
        self._settings.sync()
