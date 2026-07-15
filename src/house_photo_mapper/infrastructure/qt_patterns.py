"""Qt Memory-Safe Patterns for PySide6.

Provides base classes and utilities to prevent common PySide6 memory management issues:
- QtSafeViewModel: QObject base with enforced parent, safe signal connection
- QtSafeRunnable: QRunnable base with auto-delete disabled, explicit cleanup
- CallableSlotAdapter: Wraps any callable as a @Slot for safe signal connections
- safe_connect: Utility to connect signals safely (auto-wraps non-@Slot callables)

Reference: RESEARCH.md Pitfalls #1 (lambda memory leaks) and #5 (QRunnable auto-delete race).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QRunnable, Slot, QPointF, QPoint, Qt
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

if TYPE_CHECKING:
    from PySide6.QtCore import QObject as QObjectType

SignalInstance = Any


class QtSafeViewModel(QObject):
    """Base class for all ViewModels enforcing memory-safe Qt patterns.

    Rules enforced:
    - Parent must be passed to __init__ (or explicitly set to None for top-level)
    - All signal handlers must use @Slot() decorator
    - Use safe_connect() for connecting signals to avoid lambda leaks
    """

    def __init__(self, parent: QObjectType | None = None) -> None:
        """Initialize with required parent for Qt object tree management.

        Args:
            parent: Parent QObject for automatic cleanup. Top-level ViewModels
                may pass None but should be owned by the main window.
        """
        super().__init__(parent)

    def safe_connect(
        self,
        sender: QObjectType,
        signal: SignalInstance,
        slot: Callable[..., Any],
        *,
        connection_type: int = 0,  # Qt.ConnectionType.AutoConnection
    ) -> bool:
        """Safely connect a signal to a slot, wrapping non-@Slot callables.

        If slot is not decorated with @Slot(), wraps it in a CallableSlotAdapter
        with this ViewModel as parent, ensuring proper lifetime management.

        Args:
            sender: Object emitting the signal.
            signal: Signal to connect.
            slot: Callable to connect (will be wrapped if not @Slot decorated).
            connection_type: Qt connection type.

        Returns:
            True if connection succeeded.
        """
        if not self._is_slot_decorated(slot):
            adapter = CallableSlotAdapter(slot, parent=self)
            slot = adapter.slot

        try:
            signal.connect(slot, connection_type)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_slot_decorated(func: Callable[..., Any]) -> bool:
        """Check if a function has @Slot() decorator."""
        return hasattr(func, "__pyqt_slot__") or hasattr(func, "__slot__")


class QtSafeRunnable(QRunnable):
    """Base class for QRunnable tasks with explicit lifetime management.

    Rules enforced:
    - setAutoDelete(False) to prevent C++ side deleting while Python holds ref
    - Store reference in parent ViewModel to prevent premature GC
    """

    def __init__(self, parent: QObjectType | None = None) -> None:
        """Initialize with parent for lifetime tracking.

        Args:
            parent: Parent QObject (typically the ViewModel that owns this task).
        """
        super().__init__()
        self.setAutoDelete(False)
        self._parent = parent

    def run(self) -> None:
        """Override in subclass to implement task logic."""
        raise NotImplementedError("Subclasses must implement run()")


class CallableSlotAdapter(QObject):
    """Adapter that wraps any callable as a @Slot for safe signal connections.

    Solves the lambda/closure memory leak problem (RESEARCH.md Pitfall #1):
    Connecting `button.clicked.connect(lambda: self.do_something())` creates
    a closure that holds `self`, preventing garbage collection and causing
    segfaults when the C++ object is deleted.

    Usage:
        adapter = CallableSlotAdapter(lambda x: self.handle(x), parent=self)
        sender.signal.connect(adapter.slot)
    """

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        parent: QObjectType | None = None,
    ) -> None:
        """Create adapter for a callable.

        Args:
            func: The callable to wrap. Can be lambda, partial, or any callable.
            parent: Parent QObject for automatic cleanup when parent is deleted.
        """
        super().__init__(parent)
        self._func = func

        # Create the slot method directly on this instance
        self._create_slot()

    def _create_slot(self) -> None:
        """Create a proper @Slot method that calls the wrapped function."""

        @Slot(object)
        def _slot(*args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

        self.slot = _slot


def safe_connect(
    sender: QObjectType,
    signal: SignalInstance,
    slot: Callable[..., Any],
    *,
    parent: QObjectType | None = None,
    connection_type: int = 0,
) -> bool:
    """Connect signal to slot, auto-wrapping non-@Slot callables.

    If slot is not @Slot decorated, wraps it in a CallableSlotAdapter with
    the given parent (or sender if no parent provided).

    Args:
        sender: Object emitting the signal.
        signal: Signal to connect.
        slot: Callable to connect (will be wrapped if needed).
        parent: Parent for adapter if slot needs wrapping. Defaults to sender.
        connection_type: Qt connection type.

    Returns:
        True if connection succeeded.
    """
    if hasattr(slot, "__pyqt_slot__") or hasattr(slot, "__slot__"):
        try:
            signal.connect(slot, connection_type)
            return True
        except Exception:
            return False

    adapter_parent = parent or sender
    adapter = CallableSlotAdapter(slot, parent=adapter_parent)
    try:
        signal.connect(adapter.slot, connection_type)
        return True
    except Exception:
        return False


# =============================================================================
# Plan Viewport Classes (Phase 2)
# =============================================================================

class PlanGraphicsScene(QGraphicsScene):
    """QGraphicsScene for plan viewport with NoIndex mode.

    NoIndex is MANDATORY — default BspTreeIndex causes O(n²) degradation
    with overlapping items (plan pixmap + annotations). Linear lookup is
    fast for <100 items.
    """

    def __init__(self, parent: QObjectType | None = None) -> None:
        """Initialize scene with NoIndex mode.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        # CRITICAL: NoIndex mode prevents BSP tree degradation with
        # plan pixmap (large rect) + annotation items (overlapping)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        # Default scene rect; updated per page
        self.setSceneRect(0, 0, 1, 1)

    def set_page_size(self, width: float, height: float) -> None:
        """Update scene rect to match page size in scene coordinates.

        Args:
            width: Page width in scene units.
            height: Page height in scene units.
        """
        self.setSceneRect(0, 0, width, height)


class PlanGraphicsView(QGraphicsView):
    """Plan viewport with zoom (Ctrl+wheel), pan (middle mouse), rotate (R/Shift+R).

    Implements RESEARCH.md Pattern 3:
    - AnchorUnderMouse + viewport.mouseTracking → zoom centers on cursor
    - Middle mouse drag → translate() with scale compensation
    - R/Shift+R → rotate(±90°)
    - No scrollbars, MinimalViewportUpdate for performance
    """

    def __init__(
        self,
        scene: PlanGraphicsScene,
        parent: QObjectType | None = None,
    ) -> None:
        """Initialize plan graphics view.

        Args:
            scene: PlanGraphicsScene to display.
            parent: Parent QWidget.
        """
        super().__init__(scene, parent)

        # Annotation VM for placement
        self._annotation_vm = None
        self._pending_group = None  # AnnotationGraphicsGroup being built
        self._annotation_groups: dict[str, object] = {}  # annotation_id → group

        # Cone dragging state
        self._cone_drag_active = False
        self._cone_drag_annotation_id: str | None = None

        # Zoom centers on mouse cursor (RESEARCH.md Pitfall 5 fix)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Smooth rendering
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )

        # No drag mode - we handle pan via middle mouse
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # No scrollbars - pan via middle mouse
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Minimal viewport updates for performance
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        # CRITICAL: Mouse tracking enables AnchorUnderMouse on first wheel event
        self.viewport().setMouseTracking(True)

        # Pan state
        self._pan_active = False
        self._pan_start = QPointF()

    def set_annotation_vm(self, vm) -> None:
        """Set AnnotationViewModel for mouse event handling."""
        self._annotation_vm = vm
        if vm is not None:
            vm.annotation_added.connect(self._on_annotation_added)
            vm.annotation_removed.connect(self._on_annotation_removed)
            vm.annotations_changed.connect(self._on_annotations_changed)
            self.scene().selectionChanged.connect(self._on_scene_selection_changed)

    def _on_annotation_added(self, annotation_id: str) -> None:
        """Associate pending group with new annotation."""
        if self._pending_group is not None:
            self._pending_group.annotation_id = annotation_id
            self._annotation_groups[annotation_id] = self._pending_group
            self._pending_group = None

    def _on_annotation_removed(self, annotation_id: str) -> None:
        """Remove graphics group for deleted annotation."""
        group = self._annotation_groups.pop(annotation_id, None)
        if group is not None:
            # Remove all child items from scene
            for item in group.childItems():
                self.scene().removeItem(item)
            self.scene().removeItem(group)

    def _on_annotations_changed(self, annotation_ids: list) -> None:
        """Sync scene markers with ViewModel annotations (handles loaded annotations)."""
        if self._annotation_vm is None:
            return
        from house_photo_mapper.presentation.graphics.annotation_items import (
            AnnotationGraphicsGroup,
            CameraMarkerItem,
            DirectionArrowItem,
            ViewingConeItem,
            VisibleAreaItem,
            DEFAULT_ANNOTATION_COLOR,
        )
        for ann_id in annotation_ids:
            if ann_id not in self._annotation_groups:
                ann = self._annotation_vm.get_annotation(ann_id)
                if ann is not None:
                    self._create_annotation_group(ann, ann_id)

    def _create_annotation_group(self, ann, ann_id: str) -> None:
        """Create a full annotation group (marker + arrow + cone + rectangle)."""
        from house_photo_mapper.presentation.graphics.annotation_items import (
            AnnotationGraphicsGroup,
            CameraMarkerItem,
            DirectionArrowItem,
            ViewingConeItem,
            VisibleAreaItem,
        )

        marker = CameraMarkerItem(x=ann.position_x, y=ann.position_y)
        arrow = DirectionArrowItem(marker, angle=ann.direction_angle)
        cone = ViewingConeItem(marker, arrow, cone_angle=ann.cone_angle)

        # Create default rectangle around marker (160x120 centered on marker)
        rect_w, rect_h = 160.0, 120.0
        area = VisibleAreaItem(
            ann.position_x - rect_w / 2,
            ann.position_y - rect_h / 2,
            rect_w,
            rect_h,
        )

        group = AnnotationGraphicsGroup(annotation_id=ann_id)
        group.set_items(marker, arrow, cone, area)

        # Add all items to scene
        self.scene().addItem(area)
        self.scene().addItem(cone)
        self.scene().addItem(arrow)
        self.scene().addItem(marker)
        self.scene().addItem(group)

        # Apply color if set
        color = getattr(ann, 'color', '') or ''
        if color:
            group.set_color(color)

        cone.update_geometry()
        self._annotation_groups[ann_id] = group

    def _on_scene_selection_changed(self) -> None:
        """Handle scene selection changes - select annotation in ViewModel."""
        if self._annotation_vm is None:
            return
        from house_photo_mapper.presentation.graphics.annotation_items import GripItem

        selected = self.scene().selectedItems()
        if not selected:
            self._annotation_vm.deselect_annotation()
            # Hide all grips
            for group in self._annotation_groups.values():
                group.show_area_grips(False)
            return

        # Find annotation_id for selected item
        for item in selected:
            if isinstance(item, GripItem):
                continue
            for ann_id, group in self._annotation_groups.items():
                if item == group or item in group.childItems():
                    self._annotation_vm.select_annotation(ann_id)
                    # Show grips for selected annotation's area
                    group.show_area_grips(True)
                    return

        # If nothing matched, hide grips
        for group in self._annotation_groups.values():
            group.show_area_grips(False)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel event: Ctrl+wheel zooms, two-finger scroll pans (trackpad)."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom factor 1.15 per step (smooth, not too fast)
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            event.accept()
        elif event.pixelDelta().x() != 0 or event.pixelDelta().y() != 0:
            # Trackpad two-finger drag: pixelDelta gives smooth scroll values
            delta = event.pixelDelta()
            t = self.transform()
            self.translate(delta.x() / t.m11(), delta.y() / t.m22())
            event.accept()
        else:
            # Mouse wheel without Ctrl: scroll normally
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press: middle button starts pan, left handles tools."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and self._annotation_vm is not None:
            from house_photo_mapper.presentation.viewmodels.annotation_vm import ToolState

            if self._annotation_vm.tool_state == ToolState.PLACE_MARKER:
                self._handle_place_marker(event)
                return
            elif self._annotation_vm.tool_state == ToolState.SET_CONE:
                self._handle_cone_press(event)
                return
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def _handle_place_marker(self, event: QMouseEvent) -> None:
        """Create marker, arrow, cone, and rectangle group at click position."""
        from house_photo_mapper.presentation.graphics.annotation_items import (
            AnnotationGraphicsGroup,
            CameraMarkerItem,
            DirectionArrowItem,
            ViewingConeItem,
            VisibleAreaItem,
        )

        scene_pos = self.mapToScene(event.position().toPoint())

        # Create all items for the group
        marker = CameraMarkerItem(x=scene_pos.x(), y=scene_pos.y())
        arrow = DirectionArrowItem(marker, angle=0.0)
        cone = ViewingConeItem(marker, arrow, cone_angle=60.0)

        # Default rectangle: 160x120 centered on marker
        rect_w, rect_h = 160.0, 120.0
        area = VisibleAreaItem(
            scene_pos.x() - rect_w / 2,
            scene_pos.y() - rect_h / 2,
            rect_w,
            rect_h,
        )

        group = AnnotationGraphicsGroup()
        group.set_items(marker, arrow, cone, area)

        # Add items to scene in correct z-order
        self.scene().addItem(area)
        self.scene().addItem(cone)
        self.scene().addItem(arrow)
        self.scene().addItem(marker)
        self.scene().addItem(group)

        # Store pending group — annotation_added signal will link it
        self._pending_group = group

        # Update cone geometry
        cone.update_geometry()

        # Store position in ViewModel (triggers annotation_added)
        self._annotation_vm.place_marker(scene_pos.x(), scene_pos.y())
        event.accept()

    def _handle_cone_press(self, event: QMouseEvent) -> None:
        """Start cone rotation drag from marker."""
        scene_pos = self.mapToScene(event.position().toPoint())

        # Find which annotation group's marker is closest to click
        ann_id = self._find_nearest_annotation(scene_pos)
        if ann_id is None:
            return

        self._cone_drag_active = True
        self._cone_drag_annotation_id = ann_id
        event.accept()

    def _find_nearest_annotation(self, scene_pos: QPointF) -> str | None:
        """Find annotation_id whose marker is nearest to scene_pos."""
        import math
        from house_photo_mapper.presentation.graphics.annotation_items import CameraMarkerItem

        best_id = None
        best_dist = float("inf")
        for ann_id, group in self._annotation_groups.items():
            if group.marker is not None:
                dx = group.marker.pos().x() - scene_pos.x()
                dy = group.marker.pos().y() - scene_pos.y()
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < best_dist:
                    best_dist = dist
                    best_id = ann_id
        return best_id

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move: pan or cone rotation."""
        if self._pan_active:
            delta = event.position() - self._pan_start
            # Translate in view coordinates, compensating for current scale
            t = self.transform()
            self.translate(delta.x() / t.m11(), delta.y() / t.m22())
            self._pan_start = event.position()
            event.accept()
        elif self._cone_drag_active and self._cone_drag_annotation_id:
            self._handle_cone_drag(event)
        else:
            super().mouseMoveEvent(event)

    def _handle_cone_drag(self, event: QMouseEvent) -> None:
        """Update cone angle based on mouse position relative to marker."""
        import math

        scene_pos = self.mapToScene(event.position().toPoint())
        group = self._annotation_groups.get(self._cone_drag_annotation_id)
        if group is None or group.marker is None:
            return

        marker_pos = group.marker.pos()
        dx = scene_pos.x() - marker_pos.x()
        dy = scene_pos.y() - marker_pos.y()

        # Calculate angle from marker to mouse (in degrees, 0=right, CCW)
        angle = math.degrees(math.atan2(-dy, dx))

        # Update cone direction and geometry
        if group.arrow:
            group.arrow.set_angle(angle)
        if group.cone:
            group.cone.update_geometry()

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release: end pan or cone drag."""
        if event.button() == Qt.MouseButton.MiddleButton and self._pan_active:
            self._pan_active = False
            self.unsetCursor()
            event.accept()
        elif self._cone_drag_active:
            self._cone_drag_active = False
            self._cone_drag_annotation_id = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press: R rotates 90° CW, Shift+R rotates 90° CCW."""
        if event.key() == Qt.Key.Key_R:
            angle = -90 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 90
            self.rotate(angle)
            event.accept()
        else:
            super().keyPressEvent(event)

    def get_calibration_transform(self) -> tuple[float, QPointF]:
        """Return (pixels_per_meter, scene_origin) for calibration storage.

        Scene origin in view coordinates at current transform. ppm derived
        from current scale assuming scene units = meters.

        Returns:
            Tuple of (ppm, scene_origin).
        """
        # Scene origin (0,0) mapped to view coordinates
        scene_origin = self.mapToScene(QPoint(0, 0))
        # Current scale factor (view pixels per scene unit)
        scale = self.transform().m11()
        # ppm = 1 / scale if scene units are meters
        ppm = 1.0 / scale if scale != 0 else 1.0
        return ppm, scene_origin

    def apply_viewport_culling(self) -> int:
        """Hide items outside the visible viewport rect for performance.

        When many annotations exist (100+), items far from the viewport
        don't need to be rendered. This method sets isVisible(False) on
        items outside a padded viewport rect, skipping the pixmap background.

        Returns:
            Number of items culled (hidden).
        """
        from PySide6.QtWidgets import QGraphicsPixmapItem

        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        # Pad the culling rect by 20% to avoid popping at edges
        margin_x = viewport_rect.width() * 0.2
        margin_y = viewport_rect.height() * 0.2
        cull_rect = viewport_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)

        culled = 0
        for item in self.scene().items():
            # Skip the background pixmap — always visible
            if isinstance(item, QGraphicsPixmapItem):
                item.setVisible(True)
                continue

            item_rect = item.boundingRect()
            # Map item rect to scene coordinates (handles nested groups)
            scene_rect = item.mapToScene(item_rect).boundingRect()
            visible = cull_rect.intersects(scene_rect)
            if not visible and item.isVisible():
                item.setVisible(False)
                culled += 1
            elif visible and not item.isVisible():
                item.setVisible(True)
        return culled
