"""AnnotationViewModel — manages annotation creation, selection, and metadata."""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from house_photo_mapper.domain.models.annotation import AnnotationModel
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel


class ToolState(Enum):
    """Tool modes for annotation creation."""

    SELECT = auto()
    PLACE_MARKER = auto()
    DRAW_POLYGON = auto()
    SET_DIRECTION = auto()
    SET_CONE = auto()


class AnnotationViewModel(QtSafeViewModel):
    """ViewModel for annotation creation flow and annotation management.

    Coordinates between annotation data model, graphics items, and UI.
    Manages tool state machine for the multi-step creation workflow.
    """

    annotation_added = Signal(str)       # annotation_id
    annotation_removed = Signal(str)     # annotation_id
    annotation_selected = Signal(str)    # annotation_id
    annotation_deselected = Signal()     # no annotation selected
    tool_changed = Signal(str)           # tool state name
    annotations_changed = Signal(list)   # list of annotation_ids on current page
    error_occurred = Signal(str)         # error message

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._annotations: dict[str, AnnotationModel] = {}
        self._current_page_index: int = -1
        self._current_floor: int = 0
        self._tool_state: ToolState = ToolState.SELECT
        self._selected_annotation_id: Optional[str] = None

        # Creation flow state
        self._pending_annotation: Optional[AnnotationModel] = None
        self._creation_step: int = 0

    @property
    def tool_state(self) -> ToolState:
        return self._tool_state

    @property
    def selected_annotation_id(self) -> Optional[str]:
        return self._selected_annotation_id

    @property
    def current_annotations(self) -> list[AnnotationModel]:
        """Get annotations for current page, sorted by creation order."""
        return [
            a for a in self._annotations.values()
            if a.page_index == self._current_page_index
        ]

    @Slot(str)
    def set_tool(self, tool_name: str) -> None:
        """Set active tool by name.

        Args:
            tool_name: One of 'select', 'place_marker', 'draw_polygon'.
        """
        try:
            state = ToolState[tool_name.upper()]
        except KeyError:
            self.error_occurred.emit(f"Unknown tool: {tool_name}")
            return

        if state == ToolState.PLACE_MARKER:
            self._start_creation_flow()
        elif state == ToolState.SELECT:
            self._cancel_creation_flow()

        self._tool_state = state
        self.tool_changed.emit(tool_name)

    def _start_creation_flow(self) -> None:
        """Initialize the annotation creation flow."""
        self._pending_annotation = AnnotationModel(
            page_index=self._current_page_index,
            floor=self._current_floor,
        )
        self._creation_step = 1

    def _cancel_creation_flow(self) -> None:
        """Cancel in-progress creation."""
        self._pending_annotation = None
        self._creation_step = 0

    @Slot(float, float)
    def place_marker(self, x: float, y: float) -> None:
        """Step 1: Place camera marker at position.

        Args:
            x: X coordinate on plan.
            y: Y coordinate on plan.
        """
        if self._pending_annotation is None:
            self._pending_annotation = AnnotationModel(
                page_index=self._current_page_index,
                floor=self._current_floor,
            )

        self._pending_annotation.position_x = x
        self._pending_annotation.position_y = y
        self._creation_step = 2
        self.tool_changed.emit("set_direction")

    @Slot(float)
    def set_direction(self, angle: float) -> None:
        """Step 2: Set viewing direction.

        Args:
            angle: Direction angle in degrees (0=right, CCW positive).
        """
        if self._pending_annotation is None:
            return
        self._pending_annotation.direction_angle = angle
        self._creation_step = 3
        self.tool_changed.emit("set_cone")

    @Slot(float)
    def set_cone_angle(self, angle: float) -> None:
        """Step 3: Set viewing cone angle.

        Args:
            angle: Cone spread angle in degrees.
        """
        if self._pending_annotation is None:
            return
        self._pending_annotation.cone_angle = angle
        self._creation_step = 4
        self.tool_changed.emit("draw_polygon")

    @Slot(list)
    def set_visible_area(self, points: list[list[float]]) -> None:
        """Step 4: Set visible area polygon.

        Args:
            points: List of [x, y] polygon vertices.
        """
        if self._pending_annotation is None:
            return
        if len(points) < 3:
            self.error_occurred.emit("Visible area requires at least 3 points")
            return
        self._pending_annotation.visible_area = points
        self._creation_step = 5

    @Slot(str, str, str)
    def set_metadata(self, title: str, description: str, tags_csv: str) -> None:
        """Step 5: Set annotation metadata and finalize.

        Args:
            title: Annotation title (required).
            description: Free-text description.
            tags_csv: Comma-separated tags.
        """
        if self._pending_annotation is None:
            return

        if not title.strip():
            self.error_occurred.emit("Title is required")
            return

        self._pending_annotation.title = title.strip()
        self._pending_annotation.description = description.strip()
        self._pending_annotation.tags = [
            t.strip() for t in tags_csv.split(",") if t.strip()
        ]

        self._finalize_annotation()

    def _finalize_annotation(self) -> None:
        """Save the pending annotation and reset creation state."""
        if self._pending_annotation is None:
            return

        annotation = self._pending_annotation
        self._annotations[annotation.annotation_id] = annotation
        self.annotation_added.emit(annotation.annotation_id)
        self.annotations_changed.emit([a.annotation_id for a in self.current_annotations])

        self._pending_annotation = None
        self._creation_step = 0
        self._tool_state = ToolState.SELECT
        self.tool_changed.emit("select")

    @Slot(int)
    def set_current_page(self, page_index: int) -> None:
        """Set current page and filter annotations.

        Args:
            page_index: New active page index.
        """
        self._current_page_index = page_index
        self.annotations_changed.emit([a.annotation_id for a in self.current_annotations])

    @Slot(int)
    def set_current_floor(self, floor: int) -> None:
        """Set default floor for new annotations.

        Args:
            floor: Floor number.
        """
        self._current_floor = floor

    @Slot(str)
    def select_annotation(self, annotation_id: str) -> None:
        """Select an annotation by ID.

        Args:
            annotation_id: ID of annotation to select.
        """
        if annotation_id not in self._annotations:
            self.error_occurred.emit(f"Unknown annotation: {annotation_id}")
            return
        self._selected_annotation_id = annotation_id
        self.annotation_selected.emit(annotation_id)

    @Slot()
    def deselect_annotation(self) -> None:
        """Deselect current annotation."""
        self._selected_annotation_id = None
        self.annotation_deselected.emit()

    @Slot(str)
    def delete_annotation(self, annotation_id: str) -> None:
        """Delete an annotation by ID.

        Args:
            annotation_id: ID of annotation to remove.
        """
        if annotation_id not in self._annotations:
            return
        del self._annotations[annotation_id]
        if self._selected_annotation_id == annotation_id:
            self._selected_annotation_id = None
        self.annotation_removed.emit(annotation_id)
        self.annotations_changed.emit([a.annotation_id for a in self.current_annotations])

    @Slot(str, str, str, str)
    def update_annotation_metadata(
        self, annotation_id: str, title: str, description: str, tags_csv: str
    ) -> None:
        """Update metadata for an existing annotation.

        Args:
            annotation_id: ID of annotation to update.
            title: New title (required).
            description: New description.
            tags_csv: New comma-separated tags.
        """
        if annotation_id not in self._annotations:
            self.error_occurred.emit(f"Unknown annotation: {annotation_id}")
            return

        if not title.strip():
            self.error_occurred.emit("Title is required")
            return

        annotation = self._annotations[annotation_id]
        annotation.title = title.strip()
        annotation.description = description.strip()
        annotation.tags = [t.strip() for t in tags_csv.split(",") if t.strip()]

    def get_annotation(self, annotation_id: str) -> Optional[AnnotationModel]:
        """Get annotation by ID."""
        return self._annotations.get(annotation_id)

    def get_all_annotations(self) -> list[AnnotationModel]:
        """Get all annotations."""
        return list(self._annotations.values())

    def get_annotations_for_page(self, page_index: int) -> list[AnnotationModel]:
        """Get annotations for a specific page."""
        return [a for a in self._annotations.values() if a.page_index == page_index]
