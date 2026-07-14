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
        self._pending_marker_item = None
        self._annotation_items: dict[str, list] = {}

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
        """Associate pending marker with new annotation."""
        if self._pending_marker_item is not None:
            self._annotation_items[annotation_id] = [self._pending_marker_item]
            self._pending_marker_item = None

    def _on_annotation_removed(self, annotation_id: str) -> None:
        """Remove graphics items for deleted annotation."""
        items = self._annotation_items.pop(annotation_id, [])
        for item in items:
            self.scene().removeItem(item)

    def _on_annotations_changed(self, annotation_ids: list) -> None:
        """Sync scene markers with ViewModel annotations (handles loaded annotations)."""
        if self._annotation_vm is None:
            return
        from house_photo_mapper.presentation.graphics.annotation_items import CameraMarkerItem
        for ann_id in annotation_ids:
            if ann_id not in self._annotation_items:
                ann = self._annotation_vm.get_annotation(ann_id)
                if ann is not None:
                    marker = CameraMarkerItem(x=ann.position_x, y=ann.position_y)
                    self.scene().addItem(marker)
                    self._annotation_items[ann_id] = [marker]

    def _on_scene_selection_changed(self) -> None:
        """Handle scene selection changes - select annotation in ViewModel."""
        if self._annotation_vm is None:
            return
        selected = self.scene().selectedItems()
        if not selected:
            self._annotation_vm.deselect_annotation()
            return
        # Find annotation_id for selected item (only check marker items)
        for item in selected:
            for ann_id, items in self._annotation_items.items():
                if item in items:
                    self._annotation_vm.select_annotation(ann_id)
                    return

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
        """Handle mouse press: middle button starts pan, left button places markers."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and self._annotation_vm is not None:
            from house_photo_mapper.presentation.viewmodels.annotation_vm import ToolState
            if self._annotation_vm.tool_state == ToolState.PLACE_MARKER:
                from house_photo_mapper.presentation.graphics.annotation_items import CameraMarkerItem
                scene_pos = self.mapToScene(event.position().toPoint())

                # Create marker graphics item
                marker = CameraMarkerItem(x=scene_pos.x(), y=scene_pos.y())
                self.scene().addItem(marker)
                self._pending_marker_item = marker

                # Store position in ViewModel (triggers annotation_added)
                self._annotation_vm.place_marker(scene_pos.x(), scene_pos.y())
                event.accept()
                return
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move: pan if middle button held."""
        if self._pan_active:
            delta = event.position() - self._pan_start
            # Translate in view coordinates, compensating for current scale
            t = self.transform()
            self.translate(delta.x() / t.m11(), delta.y() / t.m22())
            self._pan_start = event.position()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release: middle button ends pan."""
        if event.button() == Qt.MouseButton.MiddleButton and self._pan_active:
            self._pan_active = False
            self.unsetCursor()
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
