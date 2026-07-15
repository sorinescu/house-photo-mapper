"""Project JSON schema definition with versioning and validation.

Provides a schema_version field and structured sections for the project file format.
This module defines the canonical schema used for serialization/deserialization
of HousePhotoMapper project files (.hpmpj).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Current schema version — increment on breaking changes
SCHEMA_VERSION: int = 1


class ProjectSchemaMeta(BaseModel):
    """Project schema metadata section."""

    schema_version: int = Field(
        default=SCHEMA_VERSION,
        ge=1,
        description="Schema version for forward/backward compatibility",
    )
    created_at: str = Field(default="", description="ISO timestamp of project creation")
    modified_at: str = Field(default="", description="ISO timestamp of last modification")
    app_version: str = Field(default="0.1.0", description="App version that created the file")


class ProjectSchema(BaseModel):
    """Complete project file schema with versioning.

    This schema defines the JSON structure of .hpmpj project files.
    Each section corresponds to a domain concern. The schema_version field
    enables forward/backward compatibility checks on load.

    Sections:
        meta: Schema version, timestamps, app version
        plans: Floor plan data (pages, calibrations)
        photos: Photo metadata and EXIF data
        annotations: Camera markers, direction, visible areas
        settings: Export configuration and report layout
        ui_state: Window layout, panel sizes, last active views
    """

    meta: ProjectSchemaMeta = Field(default_factory=ProjectSchemaMeta)
    plans: list[dict[str, Any]] = Field(default_factory=list)
    photos: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
    ui_state: dict[str, Any] = Field(default_factory=dict)


def validate_schema_version(version: int) -> None:
    """Validate that a schema version is supported.

    Args:
        version: The schema version to validate.

    Raises:
        ValueError: If the version is newer than the current schema version
            (future version not supported) or less than 1.
    """
    if version < 1:
        raise ValueError(f"Schema version must be >= 1, got {version}")
    if version > SCHEMA_VERSION:
        raise ValueError(
            f"Schema version {version} is newer than supported version {SCHEMA_VERSION}. "
            "Please update HousePhotoMapper to open this project."
        )


def migrate_schema(data: dict[str, Any], from_version: int) -> dict[str, Any]:
    """Migrate project data from an older schema version to the current version.

    Currently a no-op since we are at version 1, but provides the migration
    framework for future schema changes.

    Args:
        data: Project data dictionary to migrate.
        from_version: The schema version of the input data.

    Returns:
        Migrated data dictionary at the current schema version.
    """
    validate_schema_version(from_version)

    # Future migrations go here:
    # if from_version < 2:
    #     data = _migrate_v1_to_v2(data)
    # if from_version < 3:
    #     data = _migrate_v2_to_v3(data)

    return data
