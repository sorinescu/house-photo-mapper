"""Undo commands for annotation operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Slot
from PySide6.QtGui import QUndoCommand

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel


class PlaceAnnotationCommand(QUndoCommand):
    """Command to place an annotation marker."""

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

        # Create annotation directly without going through place_marker
        ann = AnnotationModel(
            page_index=self._page_index,
            floor=self._floor,
        )
        ann.position_x = self._x
        ann.position_y = self._y
        self._vm._annotations[ann.annotation_id] = ann
        self._annotation_id = ann.annotation_id
        self._vm.annotation_added.emit(ann.annotation_id)

    def undo(self) -> None:
        """Remove the placed annotation."""
        if self._annotation_id:
            self._vm.delete_annotation(self._annotation_id)
            self._annotation_id = None


class DeleteAnnotationCommand(QUndoCommand):
    """Command to delete an annotation."""

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
        self._annotation_data = None

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
            }
        self._vm.delete_annotation(self._annotation_id)

    def undo(self) -> None:
        """Restore the deleted annotation."""
        if self._annotation_data:
            from house_photo_mapper.domain.models.annotation import AnnotationModel

            ann = AnnotationModel(
                title=self._annotation_data["title"],
                description=self._annotation_data["description"],
                tags=self._annotation_data["tags"],
                page_index=self._annotation_data["page_index"],
                floor=self._annotation_data["floor"],
            )
            ann.position_x = self._annotation_data["position_x"]
            ann.position_y = self._annotation_data["position_y"]
            ann.annotation_id = self._annotation_id
            self._vm._annotations[self._annotation_id] = ann
            self._vm.annotation_added.emit(self._annotation_id)
            self._annotation_data = None
