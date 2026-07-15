"""Tests for CameraOverlay service."""

import math
from unittest.mock import MagicMock

import pytest

from house_photo_mapper.domain.services.camera_overlay import CameraOverlay


class TestCameraOverlay:
    """Tests for CameraOverlay static methods."""

    def test_compute_cone_vertices_zero_angle(self) -> None:
        """Test cone vertices with direction_angle=0 (pointing right)."""
        left, right = CameraOverlay.compute_cone_vertices(
            center_x=100.0,
            center_y=100.0,
            direction_angle=0.0,
            cone_angle=60.0,
            cone_length=40.0,
        )
        # angle=0, half_cone=30deg -> left at +30deg, right at -30deg
        expected_left_x = 100.0 + 40.0 * math.cos(math.radians(30))
        expected_left_y = 100.0 + 40.0 * math.sin(math.radians(30))
        expected_right_x = 100.0 + 40.0 * math.cos(math.radians(-30))
        expected_right_y = 100.0 + 40.0 * math.sin(math.radians(-30))

        assert left[0] == pytest.approx(expected_left_x)
        assert left[1] == pytest.approx(expected_left_y)
        assert right[0] == pytest.approx(expected_right_x)
        assert right[1] == pytest.approx(expected_right_y)

    def test_compute_cone_vertices_ninety_degrees(self) -> None:
        """Test cone vertices with direction_angle=90 (pointing up)."""
        left, right = CameraOverlay.compute_cone_vertices(
            center_x=100.0,
            center_y=100.0,
            direction_angle=90.0,
            cone_angle=60.0,
            cone_length=40.0,
        )
        # angle=90, half_cone=30deg -> left at 120deg, right at 60deg
        expected_left_x = 100.0 + 40.0 * math.cos(math.radians(120))
        expected_left_y = 100.0 + 40.0 * math.sin(math.radians(120))
        expected_right_x = 100.0 + 40.0 * math.cos(math.radians(60))
        expected_right_y = 100.0 + 40.0 * math.sin(math.radians(60))

        assert left[0] == pytest.approx(expected_left_x)
        assert left[1] == pytest.approx(expected_left_y)
        assert right[0] == pytest.approx(expected_right_x)
        assert right[1] == pytest.approx(expected_right_y)

    def test_invalid_cone_angle(self) -> None:
        """Test ValueError raised for cone_angle <= 0."""
        with pytest.raises(ValueError, match="cone_angle"):
            CameraOverlay.compute_cone_vertices(
                center_x=100.0,
                center_y=100.0,
                direction_angle=0.0,
                cone_angle=0.0,
                cone_length=40.0,
            )

    def test_invalid_cone_length(self) -> None:
        """Test ValueError raised for cone_length <= 0."""
        with pytest.raises(ValueError, match="cone_length"):
            CameraOverlay.compute_cone_vertices(
                center_x=100.0,
                center_y=100.0,
                direction_angle=0.0,
                cone_angle=60.0,
                cone_length=-1.0,
            )

    def test_draw_camera_overlay(self) -> None:
        """Test draw_camera_overlay calls canvas methods correctly."""
        mock_canvas = MagicMock()

        CameraOverlay.draw_camera_overlay(
            c=mock_canvas,
            center_x=100.0,
            center_y=100.0,
            direction_angle=0.0,
            cone_angle=60.0,
            color="#DC2828",
            marker_radius=6,
            cone_length=40,
        )

        # Verify saveState/restoreState pattern
        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()

        # Verify circle was drawn (camera marker)
        mock_canvas.circle.assert_called_once_with(100.0, 100.0, 6, fill=1)

        # Verify line was drawn (direction arrow)
        mock_canvas.line.assert_called_once()

        # Verify beginPath/drawPath were called (cone triangle)
        mock_canvas.beginPath.assert_called_once()
        mock_canvas.drawPath.assert_called_once_with(fill=1, stroke=1)
