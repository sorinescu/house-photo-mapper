"""AnnotationViewModel - Manages annotation creation flow and state."""

from enum import Enum
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QUndoStack

from house_photo_mapper.domain.models.annotation import AnnotationModel
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel


class AnnotationTool(Enum):
    """Annotation tool states."""

    SELECT = "select"
    PLACE_MARKER = "place_marker"
    DRAW_POLYGON = "draw_polygon"


class AnnotationCreationState(Enum):
    """States for annotation creation flow."""

    IDLE = "idle"
    PLACING_MARKER = "placing_marker"
    SETTING_DIRECTION = "setting_direction"
    ADJUSTING_CONE = "adjusting_cone"
    DRAWING_POLYGON = "drawing_polygon"
    ENTERING_METADATA = "entering_metadata"
    COMPLETE = "complete"


class AnnotationViewModel(QtSafeViewModel):
    """ViewModel for annotation management.

    Handles annotation creation flow, tool state, and metadata.
    """

    # Signals
    tool_changed = Signal(str)  # tool name
    annotation_added = Signal(object)  # AnnotationModel
    annotation_removed = Signal(str)  # annotation_id
    annotation_selected = Signal(object)  # AnnotationModel or None
    creation_state_changed = Signal(str)  # state name
    floor_changed = Signal(int)  # floor number
    metadata_changed = Signal(dict)  # metadata dict
    annotations_changed = Signal()  # emitted when annotation list changes

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize AnnotationViewModel.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._annotations: list[AnnotationModel] = []
        self._current_tool = AnnotationTool.SELECT
        self._creation_state = AnnotationCreationState.IDLE
        self._current_page_index: int = 0
        self._default_floor: int = 0

        # Current annotation being created
        self._pending_annotation: Optional[AnnotationModel] = None

        # Undo stack
        self._undo_stack = QUndoStack(self)

    @property
    def undo_stack(self) -> QUndoStack:
        """Get the undo stack."""
        return self._undo_stack

    @property
    def current_tool(self) -> AnnotationTool:
        """Get current tool."""
        return self._current_tool

    @property
    def creation_state(self) -> AnnotationCreationState:
        """Get current creation state."""
        return self._creation_state

    @property
    def annotations(self) -> list[AnnotationModel]:
        """Get all annotations."""
        return self._annotations

    def get_annotations_for_page(self, page_index: int) -> list[AnnotationModel]:
        """Get annotations for a specific page.

        Args:
            page_index: Page index to filter by.

        Returns:
            List of annotations on that page.
        """
        return [a for a in self._annotations if a.page_index == page_index]

    @Slot(str)
    def set_tool(self, tool_name: str) -> None:
        """Set current tool.

        Args:
            tool_name: Tool name ('select', 'place_marker', 'draw_polygon').
        """
        try:
            tool = AnnotationTool(tool_name)
            if tool != self._current_tool:
                self._current_tool = tool
                self.tool_changed.emit(tool_name)

                # Reset creation state when switching tools
                if tool != AnnotationTool.SELECT:
                    self._creation_state = AnnotationCreationState.IDLE
                    self._pending_annotation = None
        except ValueError:
            pass

    @Slot(int)
    def set_current_page(self, page_index: int) -> None:
        """Set current page index.

        Args:
            page_index: New page index.
        """
        self._current_page_index = page_index

    @Slot(int)
    def set_default_floor(self, floor: int) -> None:
        """Set default floor for new annotations.

        Args:
            floor: Floor number (-2 to 10).
        """
        if -2 <= floor <= 10:
            self._default_floor = floor
            self.floor_changed.emit(floor)

    def start_creation(self, photo_path: str) -> None:
        """Start annotation creation flow.

        Args:
            photo_path: Path to photo being annotated.
        """
        self._pending_annotation = AnnotationModel(
            photo_path=photo_path,
            page_index=self._current_page_index,
            floor=self._default_floor,
            position_x=0.0,
            position_y=0.0,
        )
        self._creation_state = AnnotationCreationState.PLACING_MARKER
        self.creation_state_changed.emit(self._creation_state.value)
        self.set_tool("place_marker")

    @Slot(float, float)
    def place_marker(self, x: float, y: float) -> None:
        """Place camera marker at position.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        if self._creation_state != AnnotationCreationState.PLACING_MARKER:
            return

        if self._pending_annotation is None:
            return

        self._pending_annotation.position_x = x
        self._pending_annotation.position_y = y
        self._creation_state = AnnotationCreationState.SETTING_DIRECTION
        self.creation_state_changed.emit(self._creation_state.value)

    @Slot(float)
    def set_direction(self, angle: float) -> None:
        """Set direction angle.

        Args:
            angle: Direction in degrees.
        """
        if self._creation_state != AnnotationCreationState.SETTING_DIRECTION:
            return

        if self._pending_annotation is None:
            return

        self._pending_annotation.direction_angle = angle
        self._creation_state = AnnotationCreationState.ADJUSTING_CONE
        self.creation_state_changed.emit(self._creation_state.value)

    @Slot(float)
    def set_cone_angle(self, angle: float) -> None:
        """Set cone angle.

        Args:
            angle: Cone opening angle in degrees.
        """
        if self._creation_state != AnnotationCreationState.ADJUSTING_CONE:
            return

        if self._pending_annotation is None:
            return

        self._pending_annotation.cone_angle = angle
        self._creation_state = AnnotationCreationState.DRAWING_POLYGON
        self.creation_state_changed.emit(self._creation_state.value)

    @Slot(list)
    def set_visible_area(self, points: list[tuple[float, float]]) -> None:
        """Set visible area polygon.

        Args:
            points: List of (x, y) tuples.
        """
        if self._creation_state != AnnotationCreationState.DRAWING_POLYGON:
            return

        if self._pending_annotation is None:
            return

        self._pending_annotation.visible_area = points
        self._creation_state = AnnotationCreationState.ENTERING_METADATA
        self.creation_state_changed.emit(self._creation_state.value)

    @Slot(str, str, str)
    def set_metadata(self, title: str, description: str, tags_str: str) -> None:
        """Set annotation metadata.

        Args:
            title: Annotation title.
            description: Description text.
            tags_str: Comma-separated tags.
        """
        if self._creation_state != AnnotationCreationState.ENTERING_METADATA:
            return

        if self._pending_annotation is None:
            return

        # Validate required fields
        if not title.strip():
            return

        self._pending_annotation.title = title.strip()
        self._pending_annotation.description = description.strip()
        self._pending_annotation.tags = [
            t.strip() for t in tags_str.split(",") if t.strip()
        ]

        self.metadata_changed.emit({
            "title": self._pending_annotation.title,
            "description": self._pending_annotation.description,
            "tags": self._pending_annotation.tags,
        })

    def complete_creation(self) -> Optional[AnnotationModel]:
        """Complete annotation creation and add to list.

        Returns:
            Completed AnnotationModel or None if not ready.
        """
        if self._creation_state != AnnotationCreationState.ENTERING_METADATA:
            return None

        if self._pending_annotation is None:
            return None

        # Add to annotations list
        annotation = self._pending_annotation
        self._annotations.append(annotation)

        # Reset state
        self._pending_annotation = None
        self._creation_state = AnnotationCreationState.COMPLETE
        self.creation_state_changed.emit(self._creation_state.value)

        # Emit signals
        self.annotation_added.emit(annotation)
        self.annotations_changed.emit()

        # Return to select tool
        self.set_tool("select")

        return annotation

    def cancel_creation(self) -> None:
        """Cancel current annotation creation."""
        self._pending_annotation = None
        self._creation_state = AnnotationCreationState.IDLE
        self.creation_state_changed.emit(self._creation_state.value)
        self.set_tool("select")

    @Slot(str)
    def select_annotation(self, annotation_id: str) -> None:
        """Select an annotation by ID.

        Args:
            annotation_id: Annotation to select.
        """
        for annotation in self._annotations:
            if annotation.annotation_id == annotation_id:
                self.annotation_selected.emit(annotation)
                return
        self.annotation_selected.emit(None)

    @Slot(str)
    def remove_annotation(self, annotation_id: str) -> None:
        """Remove an annotation by ID.

        Args:
            annotation_id: Annotation to remove.
        """
        for i, annotation in enumerate(self._annotations):
            if annotation.annotation_id == annotation_id:
                removed = self._annotations.pop(i)
                self.annotation_removed.emit(annotation_id)
                self.annotations_changed.emit()
                return

    def set_annotations(self, annotations: list[AnnotationModel]) -> None:
        """Set all annotations (for loading from persistence).

        Args:
            annotations: List of annotations.
        """
        self._annotations = annotations
        self.annotations_changed.emit()

    @Slot(str, str, str)
    def update_metadata(self, annotation_id: str, title: str, description: str, tags_str: str) -> None:
        """Update annotation metadata.

        Args:
            annotation_id: Annotation to update.
            title: New title.
            description: New description.
            tags_str: Comma-separated tags.
        """
        for annotation in self._annotations:
            if annotation.annotation_id == annotation_id:
                annotation.title = title.strip()
                annotation.description = description.strip()
                annotation.tags = [
                    t.strip() for t in tags_str.split(",") if t.strip()
                ]
                self.annotations_changed.emit()
                return

    @Slot(str, int)
    def update_floor(self, annotation_id: str, floor: int) -> None:
        """Update annotation floor.

        Args:
            annotation_id: Annotation to update.
            floor: New floor number.
        """
        if -2 <= floor <= 10:
            for annotation in self._annotations:
                if annotation.annotation_id == annotation_id:
                    annotation.floor = floor
                    self.annotations_changed.emit()
                    return
