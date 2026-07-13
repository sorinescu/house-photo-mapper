"""CalibrationViewModel: Manages the 5-step calibration wizard state machine.

Steps: spec → point1 → point2 → verify → complete

The ViewModel handles:
- Unit conversion (meters, feet, inches → meters)
- Point capture from PlanGraphicsView event filter
- Calibration computation via CalibrationService
- Verification with error reporting
"""

from __future__ import annotations

from enum import IntEnum, auto

from PySide6.QtCore import QPointF, Signal, Slot

from house_photo_mapper.domain.services.calibration import CalibrationService
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel


class CalibrationStep(IntEnum):
    """Steps in the calibration wizard."""

    SPEC = 0      # Enter known dimension
    POINT1 = 1    # Click first endpoint on plan
    POINT2 = 2    # Click second endpoint on plan
    VERIFY = 3    # Enter second dimension + click verify points
    COMPLETE = 4  # Calibration complete


# Unit conversion factors to meters
UNIT_TO_METERS = {
    "meters": 1.0,
    "feet": 0.3048,
    "inches": 0.0254,
}


class CalibrationViewModel(QtSafeViewModel):
    """ViewModel for the calibration dialog wizard.

    Manages 5-step wizard state. Emits signals for UI updates.
    Connects to PlanGraphicsView event filter for point capture.
    """

    # Signals
    step_changed = Signal(int)              # Emits new CalibrationStep value
    calibration_ready = Signal(object)      # Emits CalibrationModel on accept
    cancelled = Signal()                    # Emits when user cancels
    error_message = Signal(str)             # Emits validation error messages

    def __init__(self, parent=None) -> None:
        """Initialize CalibrationViewModel.

        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._step = CalibrationStep.SPEC
        self._known_distance_m: float = 0.0
        self._calibration = None  # CalibrationModel or None
        self._error_pct: float | None = None
        self._point1: QPointF | None = None
        self._point2: QPointF | None = None
        self._verify_point1: QPointF | None = None
        self._verify_point2: QPointF | None = None
        self._verify_distance_m: float = 0.0

    @property
    def step(self) -> CalibrationStep:
        """Current wizard step."""
        return self._step

    @property
    def known_distance_m(self) -> float:
        """Known distance in meters."""
        return self._known_distance_m

    @property
    def calibration(self):
        """Current CalibrationModel or None."""
        return self._calibration

    @property
    def error_pct(self) -> float | None:
        """Verification error percentage or None."""
        return self._error_pct

    def _set_step(self, step: CalibrationStep) -> None:
        """Set step and emit signal."""
        self._step = step
        self.step_changed.emit(int(step))

    @Slot(float, str)
    def set_known_distance(self, distance: float, unit: str = "meters") -> None:
        """Set known distance with unit conversion.

        Args:
            distance: Known real-world distance.
            unit: Unit of measurement ("meters", "feet", "inches").
        """
        if distance <= 0:
            self.error_message.emit("Distance must be greater than zero")
            return

        conversion = UNIT_TO_METERS.get(unit)
        if conversion is None:
            self.error_message.emit(f"Unknown unit: {unit}")
            return

        self._known_distance_m = distance * conversion
        self._set_step(CalibrationStep.POINT1)

    @Slot(QPointF)
    def receive_point(self, point: QPointF) -> None:
        """Receive a clicked point from PlanGraphicsView.

        Points are captured in scene coordinates via the event filter
        on PlanGraphicsView.mapToScene().

        Args:
            point: Clicked position in scene coordinates.
        """
        if self._step == CalibrationStep.POINT1:
            self._point1 = point
            self._set_step(CalibrationStep.POINT2)

        elif self._step == CalibrationStep.POINT2:
            self._point2 = point
            # Compute calibration
            self._calibration = CalibrationService.calibrate(
                self._point1, self._point2, self._known_distance_m
            )
            self._set_step(CalibrationStep.VERIFY)

        elif self._step == CalibrationStep.VERIFY:
            if self._verify_point1 is None:
                self._verify_point1 = point
            else:
                self._verify_point2 = point

    @Slot()
    def request_verification(self) -> None:
        """Request verification with the captured verify points.

        Compares measured distance against known distance.
        If error <= 2%, advances to COMPLETE step.
        """
        if self._calibration is None:
            self.error_message.emit("No calibration to verify")
            return

        if self._verify_point1 is None or self._verify_point2 is None:
            self.error_message.emit("Click two verification points first")
            return

        # Compute error percentage manually for reporting
        import math

        dx = self._verify_point2.x() - self._verify_point1.x()
        dy = self._verify_point2.y() - self._verify_point1.y()
        pixel_dist = math.hypot(dx, dy)
        measured_m = pixel_dist / self._calibration.pixels_per_meter
        self._error_pct = abs(measured_m - self._known_distance_m) / self._known_distance_m * 100

        # Use CalibrationService.verify to set the verified flag
        result = CalibrationService.verify(
            self._calibration,
            self._verify_point1,
            self._verify_point2,
            self._known_distance_m,
        )

        if result:
            self._set_step(CalibrationStep.COMPLETE)
        # If failed, stay on VERIFY step

    @Slot()
    def accept(self) -> None:
        """Accept the calibration and emit calibration_ready signal.

        Only emits if calibration is verified.
        """
        if self._calibration is None or not self._calibration.verified:
            self.error_message.emit("Calibration must be verified before accepting")
            return

        self.calibration_ready.emit(self._calibration)

    @Slot()
    def cancel(self) -> None:
        """Cancel the calibration wizard."""
        self.cancelled.emit()
