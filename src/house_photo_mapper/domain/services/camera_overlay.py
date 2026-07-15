"""CameraOverlay: Camera symbol and viewing cone drawing math."""

from __future__ import annotations

import math

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


class CameraOverlay:
    """Stateless service for computing camera symbol and viewing cone geometry.

    All methods are static — no state is held between calls. Overlay
    operates entirely in PDF point coordinates.
    """

    @staticmethod
    def compute_cone_vertices(
        center_x: float,
        center_y: float,
        direction_angle: float,
        cone_angle: float,
        cone_length: float,
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Compute left and right vertices of viewing cone triangle.

        Args:
            center_x: Camera X position in PDF points.
            center_y: Camera Y position in PDF points.
            direction_angle: Viewing direction in degrees (0=right, CCW).
            cone_angle: Cone spread angle in degrees.
            cone_length: Length of cone in PDF points.

        Returns:
            Tuple of (left_vertex, right_vertex) as (x, y) tuples.

        Raises:
            ValueError: If cone_angle <= 0 or cone_length <= 0.
        """
        if cone_angle <= 0:
            raise ValueError("cone_angle must be > 0")
        if cone_length <= 0:
            raise ValueError("cone_length must be > 0")

        rad = math.radians(direction_angle)
        half_cone = math.radians(cone_angle / 2)

        left_rad = rad + half_cone
        right_rad = rad - half_cone

        left = (
            center_x + cone_length * math.cos(left_rad),
            center_y + cone_length * math.sin(left_rad),
        )
        right = (
            center_x + cone_length * math.cos(right_rad),
            center_y + cone_length * math.sin(right_rad),
        )

        return left, right

    @staticmethod
    def draw_camera_overlay(
        c: canvas.Canvas,
        center_x: float,
        center_y: float,
        direction_angle: float,
        cone_angle: float,
        color: str = "#DC2828",
        marker_radius: float = 6,
        cone_length: float = 40,
    ) -> None:
        """Draw camera symbol and viewing cone on a ReportLab canvas.

        Args:
            c: ReportLab canvas to draw on.
            center_x: Camera X position in PDF points.
            center_y: Camera Y position in PDF points.
            direction_angle: Viewing direction in degrees (0=right, CCW).
            cone_angle: Cone spread angle in degrees.
            color: Hex color string for all overlay elements.
            marker_radius: Radius of the camera marker circle.
            cone_length: Length of the viewing cone in PDF points.
        """
        c.saveState()

        # Camera marker (filled circle)
        c.setFillColor(HexColor(color))
        c.circle(center_x, center_y, marker_radius, fill=1)

        # Direction arrow
        rad = math.radians(direction_angle)
        dx = 20 * math.cos(rad)
        dy = 20 * math.sin(rad)
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(2)
        c.line(center_x, center_y, center_x + dx, center_y + dy)

        # Viewing cone (triangle)
        left, right = CameraOverlay.compute_cone_vertices(
            center_x, center_y, direction_angle, cone_angle, cone_length
        )

        c.setFillColor(HexColor(color + "1A"))  # ~10% opacity
        c.setStrokeColor(HexColor(color + "99"))  # ~60% opacity
        c.setLineWidth(1)
        c.setDash(3, 2)  # dashed line
        c.beginPath()
        c.moveTo(center_x, center_y)
        c.lineTo(*left)
        c.lineTo(*right)
        c.close()
        c.drawPath(fill=1, stroke=1)

        c.restoreState()
