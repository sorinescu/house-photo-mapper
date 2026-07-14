"""Annotation domain model for camera markers and visible areas."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
import uuid


class AnnotationModel(BaseModel):
    """Annotation model linking a photo to a position on a plan page.

    Attributes:
        annotation_id: Unique identifier for this annotation.
        photo_path: Path to the associated photo.
        page_index: Index of the plan page this annotation is on.
        floor: Floor number (-2 to 10).
        position_x: X coordinate of camera marker in scene coordinates.
        position_y: Y coordinate of camera marker in scene coordinates.
        direction_angle: Direction angle in degrees (0-360).
        cone_angle: Viewing cone opening angle in degrees.
        visible_area: List of [x, y] points defining the visible polygon.
        title: Annotation title.
        description: Optional description.
        tags: List of tags.
        created_at: When the annotation was created.
        updated_at: When the annotation was last updated.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    annotation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique annotation ID")
    photo_path: str = Field(description="Path to associated photo")
    page_index: int = Field(ge=0, description="Plan page index")
    floor: int = Field(default=0, ge=-2, le=10, description="Floor number (-2 to 10)")
    position_x: float = Field(description="Camera marker X coordinate")
    position_y: float = Field(description="Camera marker Y coordinate")
    direction_angle: float = Field(default=0.0, ge=0, le=360, description="Direction angle in degrees")
    cone_angle: float = Field(default=60.0, gt=0, le=180, description="Viewing cone angle in degrees")
    visible_area: list[list[float]] = Field(default_factory=list, description="Visible area polygon points")
    title: str = Field(default="", description="Annotation title")
    description: str = Field(default="", description="Optional description")
    tags: list[str] = Field(default_factory=list, description="Tags")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    def to_project_json(self) -> dict:
        """Serialize annotation model to JSON-compatible dict.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_project_json(cls, data: dict) -> "AnnotationModel":
        """Deserialize annotation model from JSON data.

        Args:
            data: Dictionary from JSON deserialization.

        Returns:
            Validated AnnotationModel instance.
        """
        return cls.model_validate(data)
