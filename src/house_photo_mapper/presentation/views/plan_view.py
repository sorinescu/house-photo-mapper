"""PlanView - QWidget integrating PlanGraphicsScene, PlanGraphicsView, and PlanViewModel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QVBoxLayout, QWidget

from house_photo_mapper.infrastructure.qt_patterns import PlanGraphicsScene, PlanGraphicsView
from house_photo_mapper.presentation.graphics.annotation_items import (
    AnnotationGraphicsGroup,
    CameraMarkerItem,
    DirectionArrowItem,
    ViewingConeItem,
)

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel
    from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel


class PlanView(QWidget):
    """Plan viewport widget combining scene, view, and view model.

    Displays plan pages from PlanViewModel, handles zoom/pan/rotate
    via PlanGraphicsView, and provides view access for calibration
    click capture.
    """

    def __init__(self, plan_vm: PlanViewModel, parent: QWidget | None = None) -> None:
        """Initialize PlanView.

        Args:
            plan_vm: PlanViewModel to bind to.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._plan_vm = plan_vm
        self._annotation_vm: AnnotationViewModel | None = None

        # Create scene and view
        self._scene = PlanGraphicsScene(self)
        self._view = PlanGraphicsView(self._scene, self)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

        # Connect ViewModel signals
        self._connect_signals()

        # Track if first pixmap has been fitted
        self._initial_fit_done = False

    def _connect_signals(self) -> None:
        """Connect PlanViewModel signals to view updates."""
        self._plan_vm.pixmap_ready.connect(self.set_scene_pixmap)
        self._plan_vm.zoom_changed.connect(self._on_zoom_changed)
        self._plan_vm.rotation_changed.connect(self._on_rotation_changed)

    def set_scene_pixmap(self, pixmap: QPixmap) -> None:
        """Clear scene and add new pixmap item, fit to view on first load.

        Args:
            pixmap: Page pixmap to display.
        """
        # Clear existing items
        self._scene.clear()

        # Add pixmap item
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(pixmap_item)

        # Set scene rect to pixmap bounds
        self._scene.setSceneRect(QRectF(pixmap.rect()))

        # Fit to view on first pixmap
        if not self._initial_fit_done:
            self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._initial_fit_done = True

    def _on_zoom_changed(self, factor: float) -> None:
        """Handle zoom change from ViewModel.

        Args:
            factor: New zoom factor.
        """
        # Reset transform and apply new scale
        self._view.resetTransform()
        self._view.scale(factor, factor)

        # Re-apply rotation if any
        if self._plan_vm.rotation != 0:
            self._view.rotate(self._plan_vm.rotation)

    def _on_rotation_changed(self, angle: int) -> None:
        """Handle rotation change from ViewModel.

        Args:
            angle: New rotation angle in degrees.
        """
        # Reset transform, apply current scale and rotation
        current_scale = self._view.transform().m11()
        self._view.resetTransform()
        self._view.scale(current_scale, current_scale)
        if angle != 0:
            self._view.rotate(angle)

    def view(self) -> PlanGraphicsView:
        """Get the PlanGraphicsView for calibration event filter attachment.

        Returns:
            PlanGraphicsView instance.
        """
        return self._view

    def scene(self) -> PlanGraphicsScene:
        """Get the PlanGraphicsScene.

        Returns:
            PlanGraphicsScene instance.
        """
        return self._scene

    def fit_in_view(self) -> None:
        """Fit current scene content to view."""
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def map_to_scene(self, view_pos: QPointF) -> QPointF:
        """Map viewport coordinates to scene coordinates.

        Args:
            view_pos: Position in viewport coordinates.

        Returns:
            Position in scene coordinates.
        """
        return self._view.mapToScene(view_pos.toPoint())

    def map_from_scene(self, scene_pos: QPointF) -> QPointF:
        """Map scene coordinates to viewport coordinates.

        Args:
            scene_pos: Position in scene coordinates.

        Returns:
            Position in viewport coordinates.
        """
        return self._view.mapFromScene(scene_pos)

    def clear(self) -> None:
        """Clear the plan view scene."""
        self._scene.clear()
        self._initial_fit_done = False

    def set_annotation_vm(self, vm: AnnotationViewModel) -> None:
        """Set AnnotationViewModel for mouse event handling.

        Args:
            vm: AnnotationViewModel to notify on mouse events.
        """
        self._annotation_vm = vm
        self._view.set_annotation_vm(vm)


if __name__ == "__main__":
    # Quick manual test
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
    vm = PlanViewModel()
    view = PlanView(vm)
    view.show()
    print("PlanView created successfully")
    sys.exit(app.exec())
