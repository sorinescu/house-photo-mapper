"""Tests for PlanModel persistence via PersistenceService."""

import pytest
from pathlib import Path

from house_photo_mapper.domain.models.plan import (
    CalibrationModel,
    PageModel,
    PlanModel,
)
from house_photo_mapper.domain.services.persistence import PersistenceService


@pytest.fixture
def persistence() -> PersistenceService:
    """Create a PersistenceService instance."""
    return PersistenceService()


@pytest.fixture
def sample_calibration() -> CalibrationModel:
    """Create a sample CalibrationModel."""
    return CalibrationModel(
        pixels_per_meter=150.0,
        verified=True,
        reference_point1=[0.0, 0.0],
        reference_point2=[200.0, 0.0],
        reference_distance_m=1.5,
    )


@pytest.fixture
def sample_plan(sample_calibration: CalibrationModel) -> PlanModel:
    """Create a sample PlanModel with two pages and calibration."""
    pages = [
        PageModel(
            source_path="floor_plan.pdf",
            page_index=0,
            rotation=0,
            floor=0,
            order=0,
            calibration=sample_calibration,
        ),
        PageModel(
            source_path="floor_plan.pdf",
            page_index=1,
            rotation=90,
            floor=1,
            order=1,
            calibration=None,
        ),
    ]
    return PlanModel(pages=pages, active_page_index=0)


class TestPlanModelPersistence:
    """Test PlanModel save/load round-trip."""

    def test_plan_model_persistence(
        self, persistence: PersistenceService, sample_plan: PlanModel, tmp_path: Path
    ) -> None:
        """Save PlanModel → load → assert all fields equal."""
        # Save
        persistence.save_plan_model(sample_plan, tmp_path)

        # Verify file exists
        plan_path = tmp_path / "plans.json"
        assert plan_path.exists()

        # Load
        loaded = persistence.load_plan_model(tmp_path)

        assert loaded is not None
        assert len(loaded.pages) == 2
        assert loaded.active_page_index == 0

        # Page 0
        p0 = loaded.pages[0]
        assert p0.source_path == "floor_plan.pdf"
        assert p0.page_index == 0
        assert p0.rotation == 0
        assert p0.floor == 0
        assert p0.order == 0
        assert p0.calibration is not None
        assert p0.calibration.pixels_per_meter == 150.0
        assert p0.calibration.verified is True
        assert p0.calibration.reference_point1 == [0.0, 0.0]
        assert p0.calibration.reference_point2 == [200.0, 0.0]
        assert p0.calibration.reference_distance_m == 1.5

        # Page 1
        p1 = loaded.pages[1]
        assert p1.source_path == "floor_plan.pdf"
        assert p1.page_index == 1
        assert p1.rotation == 90
        assert p1.floor == 1
        assert p1.order == 1
        assert p1.calibration is None

    def test_load_missing_plans_json_returns_none(
        self, persistence: PersistenceService, tmp_path: Path
    ) -> None:
        """Missing plans.json returns None."""
        result = persistence.load_plan_model(tmp_path)
        assert result is None

    def test_atomic_write(
        self, persistence: PersistenceService, sample_plan: PlanModel, tmp_path: Path
    ) -> None:
        """Atomic write: .tmp file should not exist after save."""
        persistence.save_plan_model(sample_plan, tmp_path)

        plan_path = tmp_path / "plans.json"
        tmp_path_file = plan_path.with_suffix(".tmp")
        assert plan_path.exists()
        assert not tmp_path_file.exists()

    def test_calibration_round_trip(
        self, persistence: PersistenceService, tmp_path: Path
    ) -> None:
        """CalibrationModel ppm survives save/load."""
        cal = CalibrationModel(
            pixels_per_meter=42.5,
            verified=False,
            reference_point1=[10.0, 20.0],
            reference_point2=[30.0, 40.0],
            reference_distance_m=2.0,
        )
        page = PageModel(source_path="test.pdf", page_index=0, calibration=cal)
        plan = PlanModel(pages=[page])

        persistence.save_plan_model(plan, tmp_path)
        loaded = persistence.load_plan_model(tmp_path)

        assert loaded is not None
        loaded_cal = loaded.pages[0].calibration
        assert loaded_cal is not None
        assert loaded_cal.pixels_per_meter == 42.5
        assert loaded_cal.verified is False
        assert loaded_cal.reference_point1 == [10.0, 20.0]
        assert loaded_cal.reference_point2 == [30.0, 40.0]
        assert loaded_cal.reference_distance_m == 2.0

    def test_empty_plan_model(
        self, persistence: PersistenceService, tmp_path: Path
    ) -> None:
        """Empty PlanModel saves and loads correctly."""
        plan = PlanModel()
        persistence.save_plan_model(plan, tmp_path)
        loaded = persistence.load_plan_model(tmp_path)

        assert loaded is not None
        assert len(loaded.pages) == 0
        assert loaded.active_page_index == 0

    def test_source_path_relative(
        self, persistence: PersistenceService, tmp_path: Path
    ) -> None:
        """Source paths are stored relative to project dir."""
        page = PageModel(
            source_path="subdir/plan.pdf",
            page_index=0,
        )
        plan = PlanModel(pages=[page])

        persistence.save_plan_model(plan, tmp_path)
        loaded = persistence.load_plan_model(tmp_path)

        assert loaded is not None
        assert loaded.pages[0].source_path == "subdir/plan.pdf"
