"""ProjectModel - Core domain model for HousePhotoMapper projects."""

from dataclasses import field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExportSettings(BaseModel):
    """Export configuration settings."""

    include_photos: bool = True
    include_annotations: bool = True
    image_quality: int = 85
    page_format: str = "A4"
    orientation: str = "portrait"
    dpi: int = 300


class UIPreferences(BaseModel):
    """User interface preferences per project."""

    show_grid: bool = True
    grid_spacing: float = 1.0
    snap_to_grid: bool = True
    default_pixels_per_meter: float = 100.0
    theme: str = "system"
    language: str = "en"


class ProjectModel(BaseModel):
    """Project data model with JSON serialization.

    Represents a complete HousePhotoMapper project including plans, photos,
    annotations, export settings, and UI preferences.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_encoders={Path: str},
    )

    path: str = ""
    plans: list[dict[str, Any]] = Field(default_factory=list)
    photos: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    export_settings: ExportSettings = Field(default_factory=ExportSettings)
    ui_preferences: UIPreferences = Field(default_factory=UIPreferences)
    _dirty: bool = field(default=False, init=False, repr=False)

    @classmethod
    def create_empty(cls, path: str | Path) -> "ProjectModel":
        """Create a new empty project at the given path.

        Args:
            path: File path for the new project.

        Returns:
            New ProjectModel instance with default values.
        """
        return cls(path=str(path))

    @property
    def dirty(self) -> bool:
        """Return True if project has unsaved changes."""
        return self._dirty

    def mark_dirty(self) -> None:
        """Mark project as having unsaved changes."""
        self._dirty = True

    def mark_clean(self) -> None:
        """Mark project as saved (no unsaved changes)."""
        self._dirty = False

    @property
    def project_name(self) -> str:
        """Get project name from file path."""
        if not self.path:
            return "Untitled"
        return Path(self.path).stem

    @property
    def project_directory(self) -> Path | None:
        """Get project directory path."""
        if not self.path:
            return None
        return Path(self.path).parent
