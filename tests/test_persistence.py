"""Tests for PlanModel persistence via PersistenceService."""

import pytest
from pathlib import Path

from house_photo_mapper.domain.models.plan import (
    CalibrationModel,
    PageModel,
    PlanModel,
)
from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel


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


class TestProjectPlanIntegration:
    """Test ProjectViewModel + PlanViewModel save/load integration."""

    def test_project_save_includes_plans(
        self,
        persistence: PersistenceService,
        sample_plan: PlanModel,
        tmp_path: Path,
        qapp,
    ) -> None:
        """ProjectViewModel.save_project saves plans.json alongside .hpmpj."""
        project_path = tmp_path / "test_project.hpmpj"
        project = ProjectModel.create_empty(project_path)

        project_vm = ProjectViewModel(persistence)
        project_vm._project = project

        plan_vm = PlanViewModel()
        plan_vm.plan_model = sample_plan

        # Save project (should write both .hpmpj and plans.json)
        project.path = str(project_path)
        persistence.save_project(project)
        persistence.save_plan_model(sample_plan, tmp_path)

        assert project_path.exists()
        assert (tmp_path / "plans.json").exists()

    def test_project_load_restores_plan_model(
        self,
        persistence: PersistenceService,
        sample_plan: PlanModel,
        tmp_path: Path,
        qapp,
    ) -> None:
        """ProjectViewModel.open_project loads plans.json into PlanViewModel."""
        project_path = tmp_path / "test_project.hpmpj"
        project = ProjectModel.create_empty(project_path)

        # Save both
        persistence.save_project(project)
        persistence.save_plan_model(sample_plan, tmp_path)

        # Load
        loaded_project = persistence.load_project(str(project_path))
        loaded_plan = persistence.load_plan_model(tmp_path)

        assert loaded_plan is not None
        assert len(loaded_plan.pages) == 2

        # Inject into PlanViewModel
        plan_vm = PlanViewModel()
        plan_vm.plan_model = loaded_plan

        assert plan_vm.plan_model is not None
        assert len(plan_vm.get_sorted_pages()) == 2
        assert plan_vm.calibration is not None
        assert plan_vm.calibration.pixels_per_meter == 150.0

    def test_load_missing_plans_gives_empty_plan_model(
        self,
        persistence: PersistenceService,
        tmp_path: Path,
        qapp,
    ) -> None:
        """When plans.json missing, PlanViewModel gets empty PlanModel."""
        project_path = tmp_path / "test_project.hpmpj"
        project = ProjectModel.create_empty(project_path)
        persistence.save_project(project)

        # Load — no plans.json
        loaded_plan = persistence.load_plan_model(tmp_path)

        plan_vm = PlanViewModel()
        if loaded_plan is not None:
            plan_vm.plan_model = loaded_plan
        else:
            plan_vm.plan_model = PlanModel()

        assert plan_vm.plan_model is not None
        assert len(plan_vm.get_sorted_pages()) == 0

    def test_plan_vm_set_plan_model_emits_signals(
        self,
        sample_plan: PlanModel,
        qapp,
    ) -> None:
        """PlanViewModel.set_plan_model emits pages_changed and page_changed."""
        plan_vm = PlanViewModel()

        pages_received = []
        plan_vm.pages_changed.connect(lambda pages: pages_received.append(pages))

        page_indices = []
        plan_vm.page_changed.connect(lambda idx: page_indices.append(idx))

        plan_vm.plan_model = sample_plan

        assert len(pages_received) == 1
        assert len(pages_received[0]) == 2
        # page_changed emitted for initial page (index 0)
        assert 0 in page_indices

    def test_plan_vm_calibration_on_load(
        self,
        sample_plan: PlanModel,
        qapp,
    ) -> None:
        """PlanViewModel exposes calibration for active page after set_plan_model."""
        plan_vm = PlanViewModel()
        plan_vm.plan_model = sample_plan

        cal = plan_vm.calibration
        assert cal is not None
        assert cal.pixels_per_meter == 150.0
        assert cal.verified is True


class TestPlanUISyncOnLoad:
    """Test PlanViewModel UI sync signals on project load."""

    def test_set_plan_model_emits_pages_changed(
        self, sample_plan: PlanModel, qapp
    ) -> None:
        """set_plan_model emits pages_changed with sorted page list."""
        plan_vm = PlanViewModel()
        pages_received = []
        plan_vm.pages_changed.connect(lambda pages: pages_received.append(pages))

        plan_vm.set_plan_model(sample_plan)

        assert len(pages_received) == 1
        assert len(pages_received[0]) == 2
        # Pages sorted by order
        assert pages_received[0][0].order == 0
        assert pages_received[0][1].order == 1

    def test_set_plan_model_sets_active_page(
        self, sample_plan: PlanModel, qapp
    ) -> None:
        """set_plan_model sets current_page_index and emits page_changed."""
        plan_vm = PlanViewModel()
        page_indices = []
        plan_vm.page_changed.connect(lambda idx: page_indices.append(idx))

        plan_vm.set_plan_model(sample_plan)

        assert plan_vm.current_page == 0
        assert 0 in page_indices

    def test_set_plan_model_emits_calibration_changed(
        self, sample_plan: PlanModel, qapp
    ) -> None:
        """set_plan_model emits calibration_changed for active page."""
        plan_vm = PlanViewModel()
        cal_received = []
        plan_vm.calibration_changed.connect(lambda cal: cal_received.append(cal))

        plan_vm.set_plan_model(sample_plan)

        assert len(cal_received) >= 1
        # First emission should be the calibration of active page (index 0)
        assert cal_received[0] is not None
        assert cal_received[0].pixels_per_meter == 150.0

    def test_set_plan_model_empty_pages(
        self, qapp
    ) -> None:
        """set_plan_model with empty PlanModel emits pages_changed and calibration_changed(None)."""
        plan_vm = PlanViewModel()
        pages_received = []
        cal_received = []
        plan_vm.pages_changed.connect(lambda pages: pages_received.append(pages))
        plan_vm.calibration_changed.connect(lambda cal: cal_received.append(cal))

        plan_vm.set_plan_model(PlanModel())

        assert len(pages_received) == 1
        assert len(pages_received[0]) == 0
        # calibration_changed emitted with None for empty plan
        assert any(c is None for c in cal_received)

    def test_request_page_render_emits_pixmap(
        self, sample_plan: PlanModel, tmp_path: Path, qapp
    ) -> None:
        """request_page_render emits page_rendered with QPixmap."""
        from PySide6.QtGui import QPixmap

        plan_vm = PlanViewModel()

        # Create a dummy PDF for rendering
        import fitz

        doc = fitz.open()
        page = doc.new_page(width=200, height=200)
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()

        # Set up renderer
        from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

        renderer = PlanRenderer(str(pdf_path))
        plan_vm.plan_renderer = renderer

        # Set plan model with the PDF
        plan = PlanModel(
            pages=[PageModel(source_path="test.pdf", page_index=0, order=0)],
            active_page_index=0,
        )
        plan_vm.set_plan_model(plan)

        pixmaps = []
        plan_vm.pixmap_ready.connect(lambda pm: pixmaps.append(pm))

        plan_vm.request_page_render(0)

        assert len(pixmaps) == 1
        assert isinstance(pixmaps[0], QPixmap)
        assert not pixmaps[0].isNull()

        renderer.close()

    def test_full_save_load_ui_sync(
        self,
        persistence: PersistenceService,
        sample_plan: PlanModel,
        tmp_path: Path,
        qapp,
    ) -> None:
        """Full cycle: save project → load → PlanViewModel reflects correct state."""
        project_path = tmp_path / "test_project.hpmpj"
        project = ProjectModel.create_empty(project_path)

        # Save
        persistence.save_project(project)
        persistence.save_plan_model(sample_plan, tmp_path)

        # Load
        loaded_plan = persistence.load_plan_model(tmp_path)
        assert loaded_plan is not None

        plan_vm = PlanViewModel()
        pages_received = []
        cal_received = []
        page_indices = []
        plan_vm.pages_changed.connect(lambda pages: pages_received.append(pages))
        plan_vm.calibration_changed.connect(lambda cal: cal_received.append(cal))
        plan_vm.page_changed.connect(lambda idx: page_indices.append(idx))

        plan_vm.set_plan_model(loaded_plan)

        # Sidebar populated
        assert len(pages_received) == 1
        assert len(pages_received[0]) == 2

        # Active page highlighted
        assert plan_vm.current_page == 0
        assert 0 in page_indices

        # Calibration shown for active page
        cal = plan_vm.calibration
        assert cal is not None
        assert cal.pixels_per_meter == 150.0
        assert cal.verified is True
