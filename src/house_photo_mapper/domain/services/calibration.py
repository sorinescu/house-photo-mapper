"""CalibrationService: Specification-based scale calibration with two-point verification.

Implements RESEARCH.md Pattern 5: user enters known dimension, clicks two endpoints
on plan, software computes pixels-per-meter in scene coordinates. Second known
dimension verification enforces <=2% error tolerance.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF

from house_photo_mapper.domain.models.plan import CalibrationModel


class CalibrationService:
    """Stateless service for computing and verifying plan scale calibration.

    All methods are static — no state is held between calls. Calibration
    operates entirely in scene coordinates (world units), making the result
    invariant to viewport zoom/pan/rotate.
    """

    @staticmethod
    def calibrate(
        point1: QPointF,
        point2: QPointF,
        known_distance_m: float,
    ) -> CalibrationModel:
        """Compute pixels-per-meter from two scene points and a known real-world distance.

        Args:
            point1: First reference point in scene coordinates.
            point2: Second reference point in scene coordinates.
            known_distance_m: Known real-world distance between the points in meters.

        Returns:
            CalibrationModel with computed ppm, marked as not yet verified.

        Raises:
            ValueError: If known_distance_m <= 0 or pixel distance <= 0.
        """
        if known_distance_m <= 0:
            raise ValueError("known_distance_m must be > 0")

        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        pixel_dist = math.hypot(dx, dy)

        if pixel_dist <= 0:
            raise ValueError("pixel distance must be > 0 (points are identical)")

        ppm = pixel_dist / known_distance_m

        return CalibrationModel(
            pixels_per_meter=ppm,
            verified=False,
            reference_point1=[point1.x(), point1.y()],
            reference_point2=[point2.x(), point2.y()],
            reference_distance_m=known_distance_m,
        )

    @staticmethod
    def verify(
        cal: CalibrationModel,
        point1: QPointF,
        point2: QPointF,
        known_distance_m: float,
    ) -> bool:
        """Second-dimension verification: measure another known distance.

        Compares the measured distance (via ppm) against the known distance.
        If the error is within 2% tolerance, marks calibration as verified.

        Args:
            cal: CalibrationModel to verify (modified in-place: verified flag).
            point1: First verification point in scene coordinates.
            point2: Second verification point in scene coordinates.
            known_distance_m: Known real-world distance between verification points in meters.

        Returns:
            True if verification passed (error <= 2%), False otherwise.

        Raises:
            ValueError: If known_distance_m <= 0.
        """
        if known_distance_m <= 0:
            raise ValueError("known_distance_m must be > 0")

        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        pixel_dist = math.hypot(dx, dy)

        measured_m = pixel_dist / cal.pixels_per_meter
        error_pct = abs(measured_m - known_distance_m) / known_distance_m * 100

        cal.verified = error_pct <= 2.0
        return cal.verified
