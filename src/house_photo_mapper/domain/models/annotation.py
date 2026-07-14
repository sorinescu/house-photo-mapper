"""Annotation domain model — camera markers, direction, cone, visible area."""

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AnnotationModel(BaseModel):
    """Annotation linking a camera position to a plan page.

    Stores position, direction, viewing cone, and visible area polygon
    for a single camera annotation on a floor plan page.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    annotation_id: str = Field(default_factory=lambda: str(uuid4()))
    photo_path: str = Field(default="", description="Relative path to linked photo")
    page_index: int = Field(ge=0, description="Plan page index this annotation belongs to")
    floor: int = Field(default=0, description="Floor number for this annotation")
    position_x: float = Field(default=0.0, description="Camera X position on plan")
    position_y: float = Field(default=0.0, description="Camera Y position on plan")
    direction_angle: float = Field(default=0.0, description="Viewing direction in degrees (0=right, CCW)")
    cone_angle: float = Field(default=60.0, ge=0, le=360, description="Cone spread angle in degrees")
    visible_area: list[list[float]] = Field(
        default_factory=list,
        description="Polygon vertices [[x,y], ...] for visible area",
    )
    title: str = Field(default="", description="Annotation title (required before save)")
    description: str = Field(default="", description="Free-text description")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")

    def to_project_json(self) -> dict:
        """Serialize to JSON-compatible dict for project persistence."""
        return self.model_dump(mode="json")

    @classmethod
    def from_project_json(cls, data: dict) -> "AnnotationModel":
        """Deserialize from project JSON data."""
        return cls.model_validate(data)
