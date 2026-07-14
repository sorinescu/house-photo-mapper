"""Plan domain models: PlanModel, PageModel, CalibrationModel."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List


class CalibrationModel(BaseModel):
    """Calibration model storing pixels-per-meter in scene coordinates.

    Calibration is per-page (not per-project) because architectural plans
    often have different scales per sheet. Stores reference points in scene
    coordinates so calibration is invariant to viewport zoom/pan/rotate.

    Attributes:
        pixels_per_meter: Scale factor (pixels per meter in scene coordinates). Must be > 0.
        verified: Whether calibration passed two-point verification (≤2% error).
        reference_point1: First reference point [x, y] in scene coordinates.
        reference_point2: Second reference point [x, y] in scene coordinates.
        reference_distance_m: Known real-world distance between reference points in meters. Must be > 0.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    pixels_per_meter: float = Field(gt=0, description="Pixels per meter in scene coordinates")
    verified: bool = Field(default=False, description="Whether calibration passed verification")
    reference_point1: list[float] = Field(
        min_length=2, max_length=2, description="First reference point [x, y] in scene coords"
    )
    reference_point2: list[float] = Field(
        min_length=2, max_length=2, description="Second reference point [x, y] in scene coords"
    )
    reference_distance_m: float = Field(gt=0, description="Known distance between points in meters")


class PageModel(BaseModel):
    """Single plan page model with source reference and display properties.

    Pages are sorted by `order` for display. `active_page_index` in PlanModel
    refers to the index in this sorted list.

    Attributes:
        source_path: Path to source file (PDF/PNG/JPG), relative to project directory.
        original_path: Original absolute path when imported.
        page_index: Page index within source file (for multi-page PDFs).
        rotation: Page rotation in degrees (0, 90, 180, 270).
        floor: Floor number (-2 for basement, -1 for lower ground, 0 for ground, 1-10 for upper).
        order: Display order in page navigator (lower = first).
        calibration: Optional per-page calibration. None if not yet calibrated.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    source_path: str = Field(description="Relative path to source file from project root")
    original_path: str = Field(default="", description="Original absolute path when imported")
    page_index: int = Field(ge=0, description="Page index in source document")
    rotation: int = Field(default=0, ge=0, le=270, description="Rotation in degrees (0, 90, 180, 270)")
    floor: int = Field(default=0, ge=-2, le=10, description="Floor number (-2 to 10)")
    order: int = Field(default=0, ge=0, description="Display order in navigator")
    calibration: Optional[CalibrationModel] = Field(
        default=None, description="Per-page calibration in scene coordinates"
    )

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, v: int) -> int:
        """Validate rotation is one of 0, 90, 180, 270."""
        if v not in (0, 90, 180, 270):
            raise ValueError("rotation must be 0, 90, 180, or 270")
        return v


class PlanModel(BaseModel):
    """Plan document model containing pages and active page tracking.

    The plan model stores all imported plan pages (from PDF or image files),
    their display order, floor assignments, and per-page calibrations.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    pages: List[PageModel] = Field(default_factory=list, description="List of plan pages")
    active_page_index: int = Field(default=0, ge=0, description="Index in sorted page list")

    def get_sorted_pages(self) -> List[PageModel]:
        """Return pages sorted by display order.

        Returns:
            List of pages sorted by `order` field (ascending).
        """
        return sorted(self.pages, key=lambda p: p.order)

    def get_active_page(self) -> Optional[PageModel]:
        """Get the currently active page.

        Returns:
            Active page from sorted list, or None if no pages or invalid index.
        """
        sorted_pages = self.get_sorted_pages()
        if 0 <= self.active_page_index < len(sorted_pages):
            return sorted_pages[self.active_page_index]
        return None

    def set_active_page(self, index: int) -> None:
        """Set active page by index in sorted list.

        Args:
            index: Index in sorted page list.

        Raises:
            IndexError: If index out of bounds.
        """
        sorted_pages = self.get_sorted_pages()
        if not 0 <= index < len(sorted_pages):
            raise IndexError(f"Active page index {index} out of range [0, {len(sorted_pages)})")
        self.active_page_index = index

    def to_project_json(self) -> dict:
        """Serialize plan model to JSON-compatible dict for project persistence.

        Uses Pydantic's model_dump with mode='json' for proper serialization
        of nested models and types.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_project_json(cls, data: dict) -> "PlanModel":
        """Deserialize plan model from project JSON data.

        Args:
            data: Dictionary from JSON deserialization.

        Returns:
            Validated PlanModel instance.
        """
        return cls.model_validate(data)


if __name__ == "__main__":
    # Quick manual test
    cal = CalibrationModel(
        pixels_per_meter=100.0,
        reference_point1=[0.0, 0.0],
        reference_point2=[100.0, 0.0],
        reference_distance_m=1.0,
    )
    page = PageModel(source_path="test.pdf", page_index=0, calibration=cal)
    plan = PlanModel(pages=[page])
    print("Plan JSON:", plan.to_project_json())