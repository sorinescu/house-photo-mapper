"""Undo commands for annotation operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Slot
from PySide6.QtGui import QUndoCommand

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel


class PlaceAnnotationCommand(QUndoCommand):
    """Command to place a full annotation group (marker + arrow + cone + rectangle)."""

    def __init__(
        self,
        annotation_vm: AnnotationViewModel,
        x: float,
        y: float,
        page_index: int,
        floor: str,
    ) -> None:
        """Initialize the command.

        Args:
            annotation_vm: AnnotationViewModel instance.
            x: X coordinate on plan.
            y: Y coordinate on plan.
            page_index: Page index for the annotation.
            floor: Floor for the annotation.
        """
        super().__init__("Place annotation")
        self._vm = annotation_vm
        self._x = x
        self._y = y
        self._page_index = page_index
        self._floor = floor
        self._annotation_id: str | None = None

    def redo(self) -> None:
        """Place the annotation."""
        from house_photo_mapper.domain.models.annotation import AnnotationModel

        ann = AnnotationModel(
            page_index=self._page_index,
            floor=self._floor,
        )
        ann.position_x = self._x
        ann.position_y = self._y
        self._vm._annotations[ann.annotation_id] = ann
        self._annotation_id = ann.annotation_id
        self._vm.annotation_added.emit(ann.annotation_id)
        self._vm.annotations_changed.emit(
            [a.annotation_id for a in self._vm.current_annotations]
        )

    def undo(self) -> None:
        """Remove the placed annotation."""
        if self._annotation_id:
            self._vm.delete_annotation(self._annotation_id)
            self._annotation_id = None


class DeleteAnnotationCommand(QUndoCommand):
    """Command to delete an annotation and all its grouped items."""

    def __init__(
        self,
        annotation_vm: AnnotationViewModel,
        annotation_id: str,
    ) -> None:
        """Initialize the command.

        Args:
            annotation_vm: AnnotationViewModel instance.
            annotation_id: ID of annotation to delete.
        """
        super().__init__("Delete annotation")
        self._vm = annotation_vm
        self._annotation_id = annotation_id
        self._annotation_data: dict | None = None

    def redo(self) -> None:
        """Delete the annotation."""
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            self._annotation_data = {
                "title": ann.title,
                "description": ann.description,
                "tags": ann.tags.copy() if ann.tags else [],
                "position_x": ann.position_x,
                "position_y": ann.position_y,
                "page_index": ann.page_index,
                "floor": ann.floor,
                "cone_angle": ann.cone_angle,
                "direction_angle": ann.direction_angle,
                "color": ann.color,
            }
        self._vm.delete_annotation(self._annotation_id)

    def undo(self) -> None:
        """Restore the deleted annotation with all grouped items."""
        if self._annotation_data:
            from house_photo_mapper.domain.models.annotation import AnnotationModel

            ann = AnnotationModel(
                title=self._annotation_data["title"],
                description=self._annotation_data["description"],
                tags=self._annotation_data["tags"],
                page_index=self._annotation_data["page_index"],
                floor=self._annotation_data["floor"],
                cone_angle=self._annotation_data.get("cone_angle", 60.0),
                direction_angle=self._annotation_data.get("direction_angle", 0.0),
                color=self._annotation_data.get("color", "#DC2828"),
            )
            ann.position_x = self._annotation_data["position_x"]
            ann.position_y = self._annotation_data["position_y"]
            ann.annotation_id = self._annotation_id
            self._vm._annotations[self._annotation_id] = ann
            self._vm.annotation_added.emit(self._annotation_id)
            self._vm.annotations_changed.emit(
                [a.annotation_id for a in self._vm.current_annotations]
            )
            self._annotation_data = None


class MoveMarkerCommand(QUndoCommand):
    """Command for marker drag operations with merge compression."""

    def __init__(
        self,
        annotation_vm: AnnotationViewModel,
        annotation_id: str,
        old_x: float,
        old_y: float,
        new_x: float,
        new_y: float,
    ) -> None:
        super().__init__("Move marker")
        self._vm = annotation_vm
        self._annotation_id = annotation_id
        self._old_x = old_x
        self._old_y = old_y
        self._new_x = new_x
        self._new_y = new_y

    def redo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.position_x = self._new_x
            ann.position_y = self._new_y

    def undo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.position_x = self._old_x
            ann.position_y = self._old_y

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive move operations for smooth undo."""
        if not isinstance(other, MoveMarkerCommand):
            return False
        if other._annotation_id != self._annotation_id:
            return False
        self._new_x = other._new_x
        self._new_y = other._new_y
        return True


class ResizeRectangleCommand(QUndoCommand):
    """Command for rectangle resize operations with merge compression."""

    def __init__(
        self,
        annotation_vm: AnnotationViewModel,
        annotation_id: str,
        old_rect: list[float],
        new_rect: list[float],
    ) -> None:
        super().__init__("Resize rectangle")
        self._vm = annotation_vm
        self._annotation_id = annotation_id
        self._old_rect = old_rect
        self._new_rect = new_rect

    def redo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.visible_area = [self._new_rect]

    def undo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.visible_area = [self._old_rect]

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive resize operations."""
        if not isinstance(other, ResizeRectangleCommand):
            return False
        if other._annotation_id != self._annotation_id:
            return False
        self._new_rect = other._new_rect
        return True


class RotateConeCommand(QUndoCommand):
    """Command for cone rotation operations with merge compression."""

    def __init__(
        self,
        annotation_vm: AnnotationViewModel,
        annotation_id: str,
        old_angle: float,
        new_angle: float,
    ) -> None:
        super().__init__("Rotate cone")
        self._vm = annotation_vm
        self._annotation_id = annotation_id
        self._old_angle = old_angle
        self._new_angle = new_angle

    def redo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.direction_angle = self._new_angle

    def undo(self) -> None:
        ann = self._vm.get_annotation(self._annotation_id)
        if ann:
            ann.direction_angle = self._old_angle

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive rotate operations."""
        if not isinstance(other, RotateConeCommand):
            return False
        if other._annotation_id != self._annotation_id:
            return False
        self._new_angle = other._new_angle
        return True
