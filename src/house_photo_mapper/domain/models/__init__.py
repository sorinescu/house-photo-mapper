"""Domain models package."""

from house_photo_mapper.domain.models.annotation import AnnotationModel
from house_photo_mapper.domain.models.coordinate import (
    CoordinateSystem,
    CRSMismatchError,
    ScreenPoint,
    WorldPoint,
)
from house_photo_mapper.domain.models.photo import DuplicateGroup, ExifModel, PhotoModel
from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.models.project_schema import (
    SCHEMA_VERSION,
    ProjectSchema,
    ProjectSchemaMeta,
    migrate_schema,
    validate_schema_version,
)

__all__ = [
    "AnnotationModel",
    "ProjectModel",
    "CoordinateSystem",
    "CRSMismatchError",
    "WorldPoint",
    "ScreenPoint",
    "PhotoModel",
    "ExifModel",
    "DuplicateGroup",
    "SCHEMA_VERSION",
    "ProjectSchema",
    "ProjectSchemaMeta",
    "migrate_schema",
    "validate_schema_version",
]
