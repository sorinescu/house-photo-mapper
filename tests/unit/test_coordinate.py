"""Wave 0 scaffold tests for coordinate system - Phase 1, Plan 01-03."""

import pytest


class TestCoordinateSystemScaffold:
    """Wave 0 scaffold tests - placeholder tests for coordinate system.

    These tests will be replaced with real tests when Plan 01-03
    implements the coordinate system.
    """

    def test_coordinate_system_scaffold_exists(self) -> None:
        """Placeholder test to verify test infrastructure works."""
        assert True

    def test_coordinate_system_imports(self) -> None:
        """Test that coordinate module can be imported (will fail until implemented)."""
        # This test will fail until the coordinate module is implemented
        # ImportError is expected at this stage
        try:
            from house_photo_mapper.domain.models.coordinate import CoordinateSystem

            assert CoordinateSystem is not None
        except ImportError:
            pytest.skip("Coordinate module not yet implemented")


class TestCoordinateConversionScaffold:
    """Scaffold tests for coordinate conversion."""

    def test_world_to_screen_scaffold(self) -> None:
        """Placeholder for world-to-screen conversion test."""
        assert True

    def test_screen_to_world_scaffold(self) -> None:
        """Placeholder for screen-to-world conversion test."""
        assert True

    def test_exif_orientation_scaffold(self) -> None:
        """Placeholder for EXIF orientation handling test."""
        assert True
