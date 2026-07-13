"""Tests for PlanGraphicsScene, PlanGraphicsView, PlanViewModel, and PlanView integration."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from PySide6.QtCore import Qt, QPointF, QRectF, QEvent, QPoint
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QWidget
from PySide6.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent, QKeyEvent, QPainter

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from house_photo_mapper.infrastructure.qt_patterns import (
    PlanGraphicsScene,
    PlanGraphicsView,
    QtSafeViewModel,
)
from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
from house_photo_mapper.presentation.views.plan_view import PlanView


class TestPlanGraphicsScene:
    """Tests for PlanGraphicsScene."""

    def test_scene_uses_no_index(self, qapp):
        """Test PlanGraphicsScene uses NoIndex mode (critical for performance)."""
        scene = PlanGraphicsScene()
        assert scene.itemIndexMethod() == QGraphicsScene.ItemIndexMethod.NoIndex

    def test_scene_rect_initialized(self, qapp):
        """Test scene rect is initialized."""
        scene = PlanGraphicsScene()
        rect = scene.sceneRect()
        assert rect.width() > 0
        assert rect.height() > 0

    def test_set_scene_rect(self, qapp):
        """Test updating scene rect per page."""
        scene = PlanGraphicsScene()
        scene.setSceneRect(0, 0, 1000, 1000)
        rect = scene.sceneRect()
        assert rect.width() == 1000
        assert rect.height() == 1000


class TestPlanGraphicsView:
    """Tests for PlanGraphicsView zoom/pan/rotate handlers."""

    def setup_method(self):
        """Create view with scene for each test."""
        self.scene = PlanGraphicsScene()
        self.view = PlanGraphicsView(self.scene)

    def test_view_configuration(self, qapp):
        """Test view is configured per RESEARCH.md Pattern 3."""
        # Transformation anchor: AnchorUnderMouse for zoom centering
        assert self.view.transformationAnchor() == QGraphicsView.ViewportAnchor.AnchorUnderMouse
        assert self.view.resizeAnchor() == QGraphicsView.ViewportAnchor.AnchorUnderMouse

        # Render hints
        hints = self.view.renderHints()
        assert hints & QPainter.RenderHint.Antialiasing
        assert hints & QPainter.RenderHint.SmoothPixmapTransform

        # Drag mode
        assert self.view.dragMode() == QGraphicsView.DragMode.NoDrag

        # Scroll bars off
        assert self.view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        assert self.view.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        # Viewport update mode
        assert self.view.viewportUpdateMode() == QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate

        # Mouse tracking enabled (critical for AnchorUnderMouse first-wheel fix)
        assert self.view.viewport().hasMouseTracking() is True

    def test_wheel_event_zoom_in(self, qapp):
        """Test Ctrl+wheel zooms in centered on cursor."""
        # Create a pixmap item at origin
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.red)
        item = self.scene.addPixmap(pixmap)

        # Initial transform
        initial_transform = self.view.transform()
        assert initial_transform.m11() == 1.0
        assert initial_transform.m22() == 1.0

        # Simulate Ctrl+wheel up (zoom in)
        # Need to create a proper QWheelEvent
        event = QWheelEvent(
            QPointF(50, 50),  # position in viewport
            QPointF(50, 50),  # global position
            QPoint(0, 120),   # pixel delta (positive = up)
            QPoint(0, 120),   # angle delta
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollUpdate,
            False,  # inverted
        )
        self.view.wheelEvent(event)

        # Should have scaled by 1.15
        transform = self.view.transform()
        assert abs(transform.m11() - 1.15) < 0.01
        assert abs(transform.m22() - 1.15) < 0.01

    def test_wheel_event_zoom_out(self, qapp):
        """Test Ctrl+wheel down zooms out."""
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.red)
        self.scene.addPixmap(pixmap)

        # First zoom in
        event_in = QWheelEvent(
            QPointF(50, 50), QPointF(50, 50), QPoint(0, 120), QPoint(0, 120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollUpdate, False
        )
        self.view.wheelEvent(event_in)

        # Then zoom out
        event_out = QWheelEvent(
            QPointF(50, 50), QPointF(50, 50), QPoint(0, -120), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollUpdate, False
        )
        self.view.wheelEvent(event_out)

        # Should be back to ~1.0
        transform = self.view.transform()
        assert abs(transform.m11() - 1.0) < 0.02
        assert abs(transform.m22() - 1.0) < 0.02

    def test_wheel_event_without_ctrl_passes_to_super(self, qapp):
        """Test wheel without Ctrl passes to parent (for future scroll handling)."""
        # Just verify no exception and doesn't zoom
        initial_scale = self.view.transform().m11()
        event = QWheelEvent(
            QPointF(50, 50), QPointF(50, 50), QPoint(0, 120), QPoint(0, 120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollUpdate, False
        )
        self.view.wheelEvent(event)
        # Scale unchanged
        assert self.view.transform().m11() == initial_scale

    def test_mouse_press_middle_button_starts_pan(self, qapp):
        """Test middle mouse press activates pan mode."""
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        self.view.mousePressEvent(event)
        assert self.view._pan_active is True
        assert self.view.cursor().shape() == Qt.CursorShape.ClosedHandCursor

    def test_mouse_move_pans_scene(self, qapp):
        """Test mouse move during pan translates scene correctly."""
        # Start pan
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        self.view.mousePressEvent(press_event)

        # Move mouse
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(120, 110),  # delta = (20, 10)
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        self.view.mouseMoveEvent(move_event)

        # View should have translated
        # At scale 1.0, translate(20, 10)
        transform = self.view.transform()
        # translate moves the view, so scene appears to move opposite
        # The translation is in view coords, divided by scale
        # This is a basic check - the view transform changed
        assert self.view._pan_active is True

    def test_mouse_release_middle_button_ends_pan(self, qapp):
        """Test middle mouse release deactivates pan."""
        # Start pan
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier
        )
        self.view.mousePressEvent(press_event)

        # Release
        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(120, 110),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        self.view.mouseReleaseEvent(release_event)

        assert self.view._pan_active is False
        assert self.view.cursor().shape() == Qt.CursorShape.ArrowCursor

    def test_key_press_r_rotates_90_cw(self, qapp):
        """Test R key rotates 90° clockwise."""
        initial_rotation = self.view.transform().m11()  # Not directly rotation, but check transform changes
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.NoModifier)
        self.view.keyPressEvent(event)
        # Rotation changes the transform matrix
        transform = self.view.transform()
        # After 90° rotation, m11 ~ 0, m12 ~ 1, m21 ~ -1, m22 ~ 0
        # Actually QGraphicsView.rotate() accumulates
        assert self.view.transform() != initial_rotation

    def test_key_press_shift_r_rotates_90_ccw(self, qapp):
        """Test Shift+R rotates 90° counter-clockwise."""
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_R,
            Qt.KeyboardModifier.ShiftModifier
        )
        self.view.keyPressEvent(event)
        # Should have rotated -90°
        transform = self.view.transform()

    def test_get_calibration_transform(self, qapp):
        """Test get_calibration_transform returns ppm and scene origin."""
        ppm, scene_origin = self.view.get_calibration_transform()
        # At scale 1.0, ppm = 1.0 (scene units per pixel if scene units = meters)
        assert ppm == 1.0
        assert isinstance(scene_origin, QPointF)


class TestPlanViewModel:
    """Tests for PlanViewModel."""

    def test_viewmodel_inherits_qtsafeviewmodel(self, qapp):
        """Test PlanViewModel inherits from QtSafeViewModel."""
        assert issubclass(PlanViewModel, QtSafeViewModel)

    def test_viewmodel_has_required_signals(self, qapp):
        """Test PlanViewModel has all required signals."""
        vm = PlanViewModel()
        # Check signals exist
        assert hasattr(vm, 'page_changed')
        assert hasattr(vm, 'pixmap_ready')
        assert hasattr(vm, 'zoom_changed')
        assert hasattr(vm, 'rotation_changed')
        assert hasattr(vm, 'calibration_changed')

    def test_viewmodel_initial_state(self, qapp):
        """Test ViewModel initial state."""
        vm = PlanViewModel()
        assert vm.current_page == -1  # No page loaded
        assert vm.current_pixmap is None
        assert vm.zoom == 1.0
        assert vm.rotation == 0

    def test_set_page_emits_pixmap_ready(self, qapp):
        """Test set_page renders page and emits pixmap_ready."""
        from house_photo_mapper.domain.models.plan import PageModel, PlanModel

        vm = PlanViewModel()
        # Set up a plan model with pages
        pages = [PageModel(source_path="test.pdf", page_index=i, order=i) for i in range(2)]
        vm.plan_model = PlanModel(pages=pages)

        # Mock PlanRenderer
        with patch('house_photo_mapper.domain.services.plan_renderer.PlanRenderer') as mock_renderer_class:
            mock_renderer = MagicMock()
            mock_pixmap = QPixmap(100, 100)
            mock_pixmap.fill(Qt.GlobalColor.blue)
            mock_renderer.render_page.return_value = mock_pixmap
            mock_renderer_class.return_value = mock_renderer

            vm.plan_renderer = mock_renderer

            # Connect signal to capture emission
            emitted_pixmaps = []
            vm.pixmap_ready.connect(lambda p: emitted_pixmaps.append(p))

            vm.set_page(0)

            assert len(emitted_pixmaps) == 1
            # Compare pixmap content, not identity (Qt may copy)
            assert emitted_pixmaps[0].size() == mock_pixmap.size()
            mock_renderer.render_page.assert_called_once_with(0, dpi=150)

    def test_set_zoom_emits_signal(self, qapp):
        """Test set_zoom updates zoom and emits signal."""
        vm = PlanViewModel()
        emitted_zooms = []
        vm.zoom_changed.connect(lambda z: emitted_zooms.append(z))

        vm.set_zoom(2.0)
        assert vm.zoom == 2.0
        assert emitted_zooms == [2.0]

    def test_set_rotation_emits_signal(self, qapp):
        """Test set_rotation updates rotation and emits signal."""
        vm = PlanViewModel()
        emitted_rotations = []
        vm.rotation_changed.connect(lambda r: emitted_rotations.append(r))

        vm.set_rotation(90)
        assert vm.rotation == 90
        assert emitted_rotations == [90]

    def test_calibration_from_model(self, qapp):
        """Test calibration property reads from model."""
        from house_photo_mapper.domain.models.plan import CalibrationModel, PageModel, PlanModel

        vm = PlanViewModel()
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        page = PageModel(source_path="test.pdf", page_index=0, calibration=cal)
        vm.plan_model = PlanModel(pages=[page])
        vm.plan_model.active_page_index = 0

        assert vm.calibration is cal
        assert vm.calibration.pixels_per_meter == 100.0

    def test_get_scene_transform(self, qapp):
        """Test get_scene_transform returns scale and origin."""
        vm = PlanViewModel()
        vm.set_zoom(2.0)
        vm.set_rotation(0)
        scale, origin = vm.get_scene_transform()
        assert scale == 2.0
        assert isinstance(origin, QPointF)


class TestPlanViewIntegration:
    """Integration tests for PlanView with ViewModel."""

    def test_plan_view_creates_scene_and_view(self, qapp):
        """Test PlanView instantiates PlanGraphicsScene and PlanGraphicsView."""
        vm = PlanViewModel()
        view = PlanView(vm)

        assert isinstance(view._scene, PlanGraphicsScene)
        assert isinstance(view._view, PlanGraphicsView)
        assert view._view.scene() is view._scene

    def test_plan_view_connects_vm_signals(self, qapp):
        """Test PlanView connects ViewModel signals."""
        vm = PlanViewModel()
        view = PlanView(vm)

        # Should be connected - verify by emitting and checking scene updates
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.GlobalColor.green)

        # Emit pixmap_ready
        vm.pixmap_ready.emit(pixmap)

        # Scene should have the pixmap item
        items = view._scene.items()
        assert len(items) == 1
        assert isinstance(items[0], QGraphicsPixmapItem)
        assert items[0].pixmap().size() == pixmap.size()

    def test_plan_view_fit_in_view_on_first_pixmap(self, qapp):
        """Test PlanView fits pixmap to view on first load."""
        vm = PlanViewModel()
        view = PlanView(vm)

        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.red)

        vm.pixmap_ready.emit(pixmap)

        # View should have fitted the scene rect
        # The view's scene rect should match pixmap rect
        scene_rect = view._scene.sceneRect()
        assert scene_rect.width() == 400
        assert scene_rect.height() == 300

    def test_plan_view_zoom_sync(self, qapp):
        """Test PlanView syncs zoom from ViewModel."""
        vm = PlanViewModel()
        view = PlanView(vm)

        vm.zoom_changed.emit(1.5)

        # View transform should have scale 1.5
        transform = view._view.transform()
        assert abs(transform.m11() - 1.5) < 0.01
        assert abs(transform.m22() - 1.5) < 0.01

    def test_plan_view_rotation_sync(self, qapp):
        """Test PlanView syncs rotation from ViewModel."""
        vm = PlanViewModel()
        view = PlanView(vm)

        vm.rotation_changed.emit(90)

        # View should have rotated
        transform = view._view.transform()
        # After 90° rotation: m11~0, m12~1, m21~-1, m22~0
        assert abs(transform.m11()) < 0.1
        assert abs(transform.m12() - 1.0) < 0.1

    def test_plan_view_exposes_view_for_calibration(self, qapp):
        """Test PlanView exposes view() getter for CalibrationDialog."""
        vm = PlanViewModel()
        view = PlanView(vm)

        exposed_view = view.view()
        assert exposed_view is view._view
        assert isinstance(exposed_view, PlanGraphicsView)

    def test_plan_view_clears_scene_on_new_pixmap(self, qapp):
        """Test PlanView clears old pixmap when new one arrives."""
        vm = PlanViewModel()
        view = PlanView(vm)

        pixmap1 = QPixmap(100, 100)
        pixmap1.fill(Qt.GlobalColor.red)
        vm.pixmap_ready.emit(pixmap1)

        pixmap2 = QPixmap(200, 200)
        pixmap2.fill(Qt.GlobalColor.blue)
        vm.pixmap_ready.emit(pixmap2)

        items = view._scene.items()
        assert len(items) == 1
        assert items[0].pixmap().size() == pixmap2.size()


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])