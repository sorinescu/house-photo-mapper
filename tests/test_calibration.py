"""Tests for CalibrationService, CalibrationViewModel, and CalibrationDialog."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QDialogButtonBox

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from house_photo_mapper.domain.models.plan import CalibrationModel
from house_photo_mapper.domain.services.calibration import CalibrationService


# =============================================================================
# Task 1 Tests: CalibrationService
# =============================================================================


class TestCalibrationService:
    """Tests for CalibrationService calibrate() and verify() methods."""

    def test_calibrate_basic(self, qapp):
        """Test calibrate computes correct ppm from two points and known distance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)  # 100 pixels apart
        known_m = 1.0  # 1 meter

        cal = CalibrationService.calibrate(p1, p2, known_m)

        assert cal.pixels_per_meter == pytest.approx(100.0)
        assert cal.verified is False
        assert cal.reference_distance_m == pytest.approx(1.0)
        assert cal.reference_point1 == [0.0, 0.0]
        assert cal.reference_point2 == [100.0, 0.0]

    def test_calibrate_diagonal_distance(self, qapp):
        """Test calibrate uses Euclidean distance (hypot)."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(3.0, 4.0)  # 5 pixels (3-4-5 triangle)
        known_m = 1.0

        cal = CalibrationService.calibrate(p1, p2, known_m)

        assert cal.pixels_per_meter == pytest.approx(5.0)

    def test_calibrate_different_units(self, qapp):
        """Test calibrate with different known distances."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(200.0, 0.0)
        known_m = 2.0  # 2 meters

        cal = CalibrationService.calibrate(p1, p2, known_m)

        assert cal.pixels_per_meter == pytest.approx(100.0)

    def test_calibrate_zero_distance_raises(self, qapp):
        """Test calibrate raises ValueError for zero known distance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)

        with pytest.raises(ValueError, match="known_distance_m must be > 0"):
            CalibrationService.calibrate(p1, p2, 0.0)

    def test_calibrate_negative_distance_raises(self, qapp):
        """Test calibrate raises ValueError for negative known distance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)

        with pytest.raises(ValueError, match="known_distance_m must be > 0"):
            CalibrationService.calibrate(p1, p2, -1.0)

    def test_calibrate_identical_points_raises(self, qapp):
        """Test calibrate raises ValueError when points are identical (zero pixel distance)."""
        p1 = QPointF(50.0, 50.0)
        p2 = QPointF(50.0, 50.0)

        with pytest.raises(ValueError, match="pixel distance must be > 0"):
            CalibrationService.calibrate(p1, p2, 1.0)

    def test_verify_passes_within_tolerance(self, qapp):
        """Test verify passes when error is within 2% tolerance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        # Verification points: 101 pixels for 1.0m → 1.01m measured → 1% error
        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(301.0, 0.0)

        result = CalibrationService.verify(cal, v1, v2, 1.0)

        assert result is True
        assert cal.verified is True

    def test_verify_passes_just_under_boundary(self, qapp):
        """Test verify passes just under 2% error boundary (1.99%)."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        # 101.99 pixels → 1.0199m → 1.99% error (just under 2%)
        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(301.99, 0.0)

        result = CalibrationService.verify(cal, v1, v2, 1.0)

        assert result is True
        assert cal.verified is True

    def test_verify_fails_above_tolerance(self, qapp):
        """Test verify fails when error exceeds 2% tolerance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        # 103 pixels for 1.0m → 1.03m measured → 3% error
        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(303.0, 0.0)

        result = CalibrationService.verify(cal, v1, v2, 1.0)

        assert result is False
        assert cal.verified is False

    def test_verify_fails_at_2_1_percent(self, qapp):
        """Test verify fails at 2.1% error (plan requirement)."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        # 102.1 pixels → 1.021m → 2.1% error
        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(302.1, 0.0)

        result = CalibrationService.verify(cal, v1, v2, 1.0)

        assert result is False

    def test_verify_passes_at_1_9_percent(self, qapp):
        """Test verify passes at 1.9% error (plan requirement)."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        # 101.9 pixels → 1.019m → 1.9% error
        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(301.9, 0.0)

        result = CalibrationService.verify(cal, v1, v2, 1.0)

        assert result is True

    def test_verify_zero_known_distance_raises(self, qapp):
        """Test verify raises ValueError for zero known distance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)
        cal = CalibrationService.calibrate(p1, p2, 1.0)

        v1 = QPointF(200.0, 0.0)
        v2 = QPointF(300.0, 0.0)

        with pytest.raises(ValueError, match="known_distance_m must be > 0"):
            CalibrationService.verify(cal, v1, v2, 0.0)

    def test_calibration_model_serialization(self, qapp):
        """Test CalibrationModel serializes to JSON and back."""
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            verified=True,
            reference_point1=[10.0, 20.0],
            reference_point2=[110.0, 20.0],
            reference_distance_m=1.0,
        )

        # Serialize
        data = cal.model_dump(mode="json")
        assert data["pixels_per_meter"] == 100.0
        assert data["verified"] is True
        assert data["reference_point1"] == [10.0, 20.0]

        # Deserialize
        cal2 = CalibrationModel.model_validate(data)
        assert cal2.pixels_per_meter == 100.0
        assert cal2.verified is True
        assert cal2.reference_point1 == [10.0, 20.0]

    def test_calibration_model_validates_ppm_positive(self, qapp):
        """Test CalibrationModel rejects ppm <= 0."""
        with pytest.raises(Exception):
            CalibrationModel(
                pixels_per_meter=0.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=1.0,
            )

        with pytest.raises(Exception):
            CalibrationModel(
                pixels_per_meter=-1.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=1.0,
            )

    def test_calibration_model_validates_extra_forbidden(self, qapp):
        """Test CalibrationModel rejects extra fields."""
        with pytest.raises(Exception):
            CalibrationModel(
                pixels_per_meter=100.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=1.0,
                bogus_field="should fail",
            )


# =============================================================================
# Task 2 Tests: CalibrationViewModel and CalibrationDialog
# =============================================================================


class TestCalibrationViewModel:
    """Tests for CalibrationViewModel wizard state machine."""

    def test_vm_initial_state(self, qapp):
        """Test ViewModel starts in spec step with no calibration."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        assert vm.step == CalibrationStep.SPEC
        assert vm.calibration is None
        assert vm.error_pct is None

    def test_vm_set_known_distance_advances_to_point1(self, qapp):
        """Test setting known distance advances to point1 step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        assert vm.step == CalibrationStep.POINT1
        assert vm.known_distance_m == 1.0

    def test_vm_rejects_zero_distance(self, qapp):
        """Test setting zero distance stays on spec step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(0.0)
        assert vm.step == CalibrationStep.SPEC

    def test_vm_rejects_negative_distance(self, qapp):
        """Test setting negative distance stays on spec step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(-1.0)
        assert vm.step == CalibrationStep.SPEC

    def test_vm_receive_point1_advances_to_point2(self, qapp):
        """Test receiving first point advances to point2 step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(0.0, 0.0))
        assert vm.step == CalibrationStep.POINT2

    def test_vm_receive_point2_advances_to_verify(self, qapp):
        """Test receiving second point advances to verify step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(0.0, 0.0))  # point1
        vm.receive_point(QPointF(100.0, 0.0))  # point2
        assert vm.step == CalibrationStep.VERIFY
        assert vm.calibration is not None
        assert vm.calibration.pixels_per_meter == pytest.approx(100.0)

    def test_vm_verify_pass_advances_to_complete(self, qapp):
        """Test successful verification advances to complete step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(0.0, 0.0))
        vm.receive_point(QPointF(100.0, 0.0))
        # Verify with matching distance
        vm.receive_point(QPointF(200.0, 0.0))
        vm.receive_point(QPointF(300.0, 0.0))
        vm.request_verification()

        assert vm.step == CalibrationStep.COMPLETE
        assert vm.calibration.verified is True
        assert vm.error_pct == pytest.approx(0.0)

    def test_vm_verify_fail_stays_on_verify(self, qapp):
        """Test failed verification stays on verify step."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(0.0, 0.0))
        vm.receive_point(QPointF(100.0, 0.0))
        # Verify with wrong distance (10% error)
        vm.receive_point(QPointF(200.0, 0.0))
        vm.receive_point(QPointF(310.0, 0.0))
        vm.request_verification()

        assert vm.step == CalibrationStep.VERIFY
        assert vm.calibration.verified is False
        assert vm.error_pct is not None
        assert vm.error_pct > 2.0

    def test_vm_accept_emits_calibration_ready(self, qapp):
        """Test accept emits calibration_ready signal with CalibrationModel."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        emitted = []
        vm.calibration_ready.connect(lambda cal: emitted.append(cal))

        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(0.0, 0.0))
        vm.receive_point(QPointF(100.0, 0.0))
        vm.receive_point(QPointF(200.0, 0.0))
        vm.receive_point(QPointF(300.0, 0.0))
        vm.request_verification()
        vm.accept()

        assert len(emitted) == 1
        assert emitted[0].verified is True

    def test_vm_cancel_emits_cancelled(self, qapp):
        """Test cancel emits cancelled signal."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel

        vm = CalibrationViewModel()
        cancelled = []
        vm.cancelled.connect(lambda: cancelled.append(True))

        vm.cancel()

        assert len(cancelled) == 1

    def test_vm_unit_conversion_inches_to_meters(self, qapp):
        """Test unit conversion from inches to meters."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel

        vm = CalibrationViewModel()
        vm.set_known_distance(36.0, unit="inches")
        assert vm.known_distance_m == pytest.approx(0.9144)

    def test_vm_unit_conversion_feet_to_meters(self, qapp):
        """Test unit conversion from feet to meters."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel

        vm = CalibrationViewModel()
        vm.set_known_distance(3.0, unit="feet")
        assert vm.known_distance_m == pytest.approx(0.9144)

    def test_vm_unit_conversion_meters(self, qapp):
        """Test no conversion for meters."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0, unit="meters")
        assert vm.known_distance_m == pytest.approx(1.0)

    def test_vm_step_changed_signal(self, qapp):
        """Test step_changed signal emits on step transitions."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import (
            CalibrationViewModel,
            CalibrationStep,
        )

        vm = CalibrationViewModel()
        steps = []
        vm.step_changed.connect(lambda s: steps.append(s))

        vm.set_known_distance(1.0)
        assert steps == [CalibrationStep.POINT1]

    def test_vm_points_captured(self, qapp):
        """Test points are captured and stored during wizard."""
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel

        vm = CalibrationViewModel()
        vm.set_known_distance(1.0)
        vm.receive_point(QPointF(10.0, 20.0))
        vm.receive_point(QPointF(110.0, 20.0))

        assert vm._point1 == QPointF(10.0, 20.0)
        assert vm._point2 == QPointF(110.0, 20.0)


# =============================================================================
# Task 3 Tests: Integration with PlanViewModel and PlanGraphicsView
# =============================================================================


class TestCalibrationIntegration:
    """Integration tests for calibration with PlanViewModel."""

    def test_plan_vm_has_start_calibration(self, qapp):
        """Test PlanViewModel has start_calibration method."""
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel

        vm = PlanViewModel()
        assert hasattr(vm, "start_calibration")

    def test_start_calibration_opens_dialog(self, qapp):
        """Test start_calibration creates and shows CalibrationDialog."""
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PageModel, PlanModel

        vm = PlanViewModel()
        pages = [PageModel(source_path="test.pdf", page_index=0, order=0)]
        vm.plan_model = PlanModel(pages=pages)

        with patch(
            "house_photo_mapper.presentation.views.calibration_dialog.CalibrationDialog"
        ) as MockDialog, patch(
            "house_photo_mapper.presentation.viewmodels.calibration_vm.CalibrationViewModel"
        ):
            mock_instance = MagicMock()
            MockDialog.return_value = mock_instance

            vm.start_calibration()

            MockDialog.assert_called_once()
            mock_instance.exec.assert_called_once()

    def test_calibration_ready_stores_in_plan_model(self, qapp):
        """Test calibration_ready signal stores CalibrationModel in PlanModel."""
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import (
            CalibrationModel,
            PageModel,
            PlanModel,
        )

        vm = PlanViewModel()
        pages = [PageModel(source_path="test.pdf", page_index=0, order=0)]
        vm.plan_model = PlanModel(pages=pages)

        cal = CalibrationModel(
            pixels_per_meter=100.0,
            verified=True,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )

        # Simulate calibration_ready signal
        emitted = []
        vm.calibration_changed.connect(lambda c: emitted.append(c))

        vm.set_calibration(cal)

        # Verify stored in model
        active_page = vm.plan_model.get_active_page()
        assert active_page.calibration is cal
        assert emitted == [cal]

    def test_calibration_survives_model_serialization(self, qapp):
        """Test calibration survives JSON serialization round-trip."""
        from house_photo_mapper.domain.models.plan import (
            CalibrationModel,
            PageModel,
            PlanModel,
        )

        cal = CalibrationModel(
            pixels_per_meter=150.5,
            verified=True,
            reference_point1=[10.0, 20.0],
            reference_point2=[160.5, 20.0],
            reference_distance_m=1.0,
        )
        page = PageModel(source_path="floor1.pdf", page_index=0, calibration=cal)
        plan = PlanModel(pages=[page])

        # Serialize to JSON
        json_data = plan.to_project_json()

        # Deserialize
        plan2 = PlanModel.from_project_json(json_data)

        # Verify calibration survived
        page2 = plan2.pages[0]
        assert page2.calibration is not None
        assert page2.calibration.pixels_per_meter == pytest.approx(150.5)
        assert page2.calibration.verified is True
        assert page2.calibration.reference_point1 == [10.0, 20.0]

    def test_calibration_per_page_not_global(self, qapp):
        """Test calibration is per-page, not global."""
        from house_photo_mapper.domain.models.plan import (
            CalibrationModel,
            PageModel,
            PlanModel,
        )

        cal1 = CalibrationModel(
            pixels_per_meter=100.0,
            verified=True,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        cal2 = CalibrationModel(
            pixels_per_meter=200.0,
            verified=True,
            reference_point1=[0.0, 0.0],
            reference_point2=[200.0, 0.0],
            reference_distance_m=1.0,
        )

        page1 = PageModel(source_path="floor1.pdf", page_index=0, calibration=cal1)
        page2 = PageModel(source_path="floor2.pdf", page_index=1, calibration=cal2)
        plan = PlanModel(pages=[page1, page2])

        # Each page has its own calibration
        assert plan.pages[0].calibration.pixels_per_meter == 100.0
        assert plan.pages[1].calibration.pixels_per_meter == 200.0

        # Serialize/deserialize preserves per-page calibration
        json_data = plan.to_project_json()
        plan2 = PlanModel.from_project_json(json_data)
        assert plan2.pages[0].calibration.pixels_per_meter == 100.0
        assert plan2.pages[1].calibration.pixels_per_meter == 200.0

    def test_calibration_ppm_in_scene_coordinates(self, qapp):
        """Test ppm is stored in scene coordinates (invariant to view transform)."""
        from house_photo_mapper.infrastructure.qt_patterns import (
            PlanGraphicsScene,
            PlanGraphicsView,
        )

        scene = PlanGraphicsScene()
        view = PlanGraphicsView(scene)

        # At default zoom, get_calibration_transform returns scale info
        ppm, origin = view.get_calibration_transform()
        assert ppm == 1.0  # At scale 1.0, 1 scene unit per pixel

        # After zoom, the calibration transform changes but stored ppm remains the same
        view.scale(2.0, 2.0)
        ppm_zoomed, _ = view.get_calibration_transform()
        assert ppm_zoomed == pytest.approx(0.5)  # At 2x zoom, 0.5 scene units per pixel

        # But the stored calibration ppm (in scene coords) doesn't change
        # This is the key invariant: ppm is in SCENE coordinates

    def test_plan_view_exposes_view_for_calibration(self, qapp):
        """Test PlanView.view() returns PlanGraphicsView for event filter."""
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.presentation.views.plan_view import PlanView
        from house_photo_mapper.infrastructure.qt_patterns import PlanGraphicsView

        vm = PlanViewModel()
        view = PlanView(vm)

        exposed = view.view()
        assert isinstance(exposed, PlanGraphicsView)

    def test_clear_calibration(self, qapp):
        """Test clearing calibration from active page."""
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import (
            CalibrationModel,
            PageModel,
            PlanModel,
        )

        vm = PlanViewModel()
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            verified=True,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        page = PageModel(source_path="test.pdf", page_index=0, calibration=cal)
        vm.plan_model = PlanModel(pages=[page])

        assert vm.calibration is cal

        emitted = []
        vm.calibration_changed.connect(lambda c: emitted.append(c))

        vm.clear_calibration()

        assert vm.calibration is None
        assert emitted == [None]
