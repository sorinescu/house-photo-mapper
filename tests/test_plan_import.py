"""Tests for PlanModel, PageModel, CalibrationModel, and PlanRenderer."""

import pytest
from pydantic import ValidationError
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

from house_photo_mapper.domain.models.plan import (
    PageModel,
    CalibrationModel,
    PlanModel,
)
from house_photo_mapper.domain.services.plan_renderer import PlanRenderer


class TestCalibrationModel:
    """Tests for CalibrationModel Pydantic model."""

    def test_calibration_model_valid(self):
        """Test valid calibration model creation."""
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            reference_point1=[100.0, 200.0],
            reference_point2=[300.0, 200.0],
            reference_distance_m=2.0,
        )
        assert cal.pixels_per_meter == 100.0
        assert cal.reference_point1 == [100.0, 200.0]
        assert cal.reference_point2 == [300.0, 200.0]
        assert cal.reference_distance_m == 2.0
        assert cal.verified is False

    def test_calibration_model_verified_true(self):
        """Test calibration with verified=True."""
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            verified=True,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        assert cal.verified is True

    def test_calibration_model_invalid_pixels_per_meter_zero(self):
        """Test calibration rejects zero pixels_per_meter."""
        with pytest.raises(ValidationError) as exc:
            CalibrationModel(
                pixels_per_meter=0.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=1.0,
            )
        assert "greater than 0" in str(exc.value).lower() or "gt" in str(exc.value).lower()

    def test_calibration_model_invalid_pixels_per_meter_negative(self):
        """Test calibration rejects negative pixels_per_meter."""
        with pytest.raises(ValidationError) as exc:
            CalibrationModel(
                pixels_per_meter=-10.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=1.0,
            )
        assert "greater than 0" in str(exc.value).lower() or "gt" in str(exc.value).lower()

    def test_calibration_model_invalid_reference_distance_zero(self):
        """Test calibration rejects zero reference_distance_m."""
        with pytest.raises(ValidationError) as exc:
            CalibrationModel(
                pixels_per_meter=100.0,
                reference_point1=[0.0, 0.0],
                reference_point2=[100.0, 0.0],
                reference_distance_m=0.0,
            )
        assert "greater than 0" in str(exc.value).lower() or "gt" in str(exc.value).lower()

    def test_calibration_model_invalid_reference_point_length(self):
        """Test calibration rejects reference points not of length 2."""
        with pytest.raises(ValidationError) as exc:
            CalibrationModel(
                pixels_per_meter=100.0,
                reference_point1=[100.0],  # Only 1 coordinate
                reference_point2=[300.0, 200.0],
                reference_distance_m=2.0,
            )
        # Pydantic v2 error message says "too_short"
        assert "too_short" in str(exc.value).lower()

    def test_calibration_serialization_roundtrip(self):
        """Test calibration model serialization to/from JSON."""
        cal = CalibrationModel(
            pixels_per_meter=123.456,
            verified=True,
            reference_point1=[10.5, 20.5],
            reference_point2=[110.5, 20.5],
            reference_distance_m=1.0,
        )
        # Serialize to JSON
        json_data = cal.model_dump(mode="json")
        assert json_data["pixels_per_meter"] == 123.456
        assert json_data["verified"] is True
        assert json_data["reference_point1"] == [10.5, 20.5]
        assert json_data["reference_point2"] == [110.5, 20.5]
        assert json_data["reference_distance_m"] == 1.0

        # Deserialize from JSON
        cal2 = CalibrationModel.model_validate(json_data)
        assert cal2.pixels_per_meter == 123.456
        assert cal2.verified is True
        assert cal2.reference_point1 == [10.5, 20.5]
        assert cal2.reference_point2 == [110.5, 20.5]
        assert cal2.reference_distance_m == 1.0


class TestPageModel:
    """Tests for PageModel Pydantic model."""

    def test_page_model_valid_minimal(self):
        """Test minimal valid page model."""
        page = PageModel(source_path="plan.pdf", page_index=0)
        assert page.source_path == "plan.pdf"
        assert page.page_index == 0
        assert page.rotation == 0
        assert page.floor == 0
        assert page.order == 0
        assert page.calibration is None

    def test_page_model_valid_full(self):
        """Test page model with all fields."""
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        page = PageModel(
            source_path="plans/floor1.pdf",
            page_index=2,
            rotation=90,
            floor=1,
            order=5,
            calibration=cal,
        )
        assert page.source_path == "plans/floor1.pdf"
        assert page.page_index == 2
        assert page.rotation == 90
        assert page.floor == 1
        assert page.order == 5
        assert page.calibration is cal

    def test_page_model_invalid_rotation(self):
        """Test page model rejects invalid rotation values."""
        with pytest.raises(ValidationError) as exc:
            PageModel(source_path="test.pdf", page_index=0, rotation=45)
        assert "rotation must be 0, 90, 180, or 270" in str(exc.value)

    def test_page_model_valid_rotations(self):
        """Test page model accepts valid rotation values."""
        for rot in [0, 90, 180, 270]:
            page = PageModel(source_path="test.pdf", page_index=0, rotation=rot)
            assert page.rotation == rot

    def test_page_model_invalid_floor_low(self):
        """Test page model rejects floor < -2."""
        with pytest.raises(ValidationError):
            PageModel(source_path="test.pdf", page_index=0, floor=-3)

    def test_page_model_invalid_floor_high(self):
        """Test page model rejects floor > 10."""
        with pytest.raises(ValidationError):
            PageModel(source_path="test.pdf", page_index=0, floor=11)

    def test_page_model_valid_floors(self):
        """Test page model accepts valid floor range -2 to 10."""
        for floor in [-2, -1, 0, 1, 5, 10]:
            page = PageModel(source_path="test.pdf", page_index=0, floor=floor)
            assert page.floor == floor

    def test_page_model_calibration_optional(self):
        """Test calibration field is optional and defaults to None."""
        page = PageModel(source_path="test.pdf", page_index=0)
        assert page.calibration is None

    def test_page_model_validate_assignment(self):
        """Test validate_assignment works on PageModel."""
        page = PageModel(source_path="test.pdf", page_index=0)
        # Valid assignment
        page.rotation = 180
        assert page.rotation == 180
        # Invalid assignment should raise
        with pytest.raises(ValidationError):
            page.rotation = 45

    def test_page_model_extra_forbidden(self):
        """Test extra fields are forbidden."""
        with pytest.raises(ValidationError):
            PageModel(source_path="test.pdf", page_index=0, extra_field="not allowed")


class TestPlanModel:
    """Tests for PlanModel Pydantic model."""

    def test_plan_model_empty(self):
        """Test empty plan model."""
        plan = PlanModel()
        assert plan.pages == []
        assert plan.active_page_index == 0

    def test_plan_model_with_pages(self):
        """Test plan model with pages."""
        pages = [
            PageModel(source_path="page1.pdf", page_index=0, order=0),
            PageModel(source_path="page2.pdf", page_index=1, order=1),
        ]
        plan = PlanModel(pages=pages)
        assert len(plan.pages) == 2
        assert plan.active_page_index == 0

    def test_plan_model_sorted_pages(self):
        """Test get_sorted_pages returns pages sorted by order."""
        pages = [
            PageModel(source_path="page3.pdf", page_index=2, order=2),
            PageModel(source_path="page1.pdf", page_index=0, order=0),
            PageModel(source_path="page2.pdf", page_index=1, order=1),
        ]
        plan = PlanModel(pages=pages)
        sorted_pages = plan.get_sorted_pages()
        assert [p.source_path for p in sorted_pages] == ["page1.pdf", "page2.pdf", "page3.pdf"]

    def test_plan_model_get_active_page(self):
        """Test get_active_page returns correct page from sorted list."""
        pages = [
            PageModel(source_path="page2.pdf", page_index=1, order=1),
            PageModel(source_path="page1.pdf", page_index=0, order=0),
        ]
        plan = PlanModel(pages=pages, active_page_index=0)
        active = plan.get_active_page()
        assert active.source_path == "page1.pdf"  # First in sorted order

        plan.active_page_index = 1
        active = plan.get_active_page()
        assert active.source_path == "page2.pdf"  # Second in sorted order

    def test_plan_model_get_active_page_invalid_index(self):
        """Test get_active_page returns None for invalid index."""
        plan = PlanModel(pages=[PageModel(source_path="test.pdf", page_index=0)])
        plan.active_page_index = 5
        assert plan.get_active_page() is None

        # Note: setting to -1 raises ValidationError due to validate_assignment
        # This is expected behavior
        with pytest.raises(ValidationError):
            plan.active_page_index = -1

    def test_plan_model_set_active_page(self):
        """Test set_active_page updates index."""
        pages = [
            PageModel(source_path="page1.pdf", page_index=0, order=0),
            PageModel(source_path="page2.pdf", page_index=1, order=1),
        ]
        plan = PlanModel(pages=pages)
        plan.set_active_page(1)
        assert plan.active_page_index == 1
        assert plan.get_active_page().source_path == "page2.pdf"

    def test_plan_model_set_active_page_invalid(self):
        """Test set_active_page raises IndexError for invalid index."""
        plan = PlanModel(pages=[PageModel(source_path="test.pdf", page_index=0)])
        with pytest.raises(IndexError):
            plan.set_active_page(5)
        with pytest.raises(IndexError):
            plan.set_active_page(-1)

    def test_plan_model_active_page_index_validation(self):
        """Test active_page_index must be >= 0."""
        with pytest.raises(ValidationError):
            PlanModel(active_page_index=-1)

    def test_plan_model_to_project_json(self):
        """Test serialization to project JSON."""
        cal = CalibrationModel(
            pixels_per_meter=100.0,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        page = PageModel(
            source_path="floor1.pdf",
            page_index=0,
            rotation=90,
            floor=1,
            order=0,
            calibration=cal,
        )
        plan = PlanModel(pages=[page], active_page_index=0)
        json_data = plan.to_project_json()

        assert json_data["active_page_index"] == 0
        assert len(json_data["pages"]) == 1
        page_data = json_data["pages"][0]
        assert page_data["source_path"] == "floor1.pdf"
        assert page_data["page_index"] == 0
        assert page_data["rotation"] == 90
        assert page_data["floor"] == 1
        assert page_data["order"] == 0
        assert page_data["calibration"]["pixels_per_meter"] == 100.0
        assert page_data["calibration"]["verified"] is False

    def test_plan_model_from_project_json(self):
        """Test deserialization from project JSON."""
        json_data = {
            "pages": [
                {
                    "source_path": "floor1.pdf",
                    "page_index": 0,
                    "rotation": 0,
                    "floor": 0,
                    "order": 0,
                    "calibration": {
                        "pixels_per_meter": 100.0,
                        "verified": True,
                        "reference_point1": [0.0, 0.0],
                        "reference_point2": [100.0, 0.0],
                        "reference_distance_m": 1.0,
                    },
                }
            ],
            "active_page_index": 0,
        }
        plan = PlanModel.from_project_json(json_data)
        assert len(plan.pages) == 1
        assert plan.pages[0].source_path == "floor1.pdf"
        assert plan.pages[0].calibration is not None
        assert plan.pages[0].calibration.pixels_per_meter == 100.0
        assert plan.pages[0].calibration.verified is True

    def test_plan_model_extra_forbidden(self):
        """Test extra fields are forbidden."""
        with pytest.raises(ValidationError):
            PlanModel(extra_field="not allowed")

    def test_plan_model_validate_assignment(self):
        """Test validate_assignment works on PlanModel."""
        plan = PlanModel()
        plan.active_page_index = 5
        assert plan.active_page_index == 5
        with pytest.raises(ValidationError):
            plan.active_page_index = -1


class TestPlanModelIntegration:
    """Integration tests for PlanModel with multiple pages and calibrations."""

    def test_multi_page_plan_with_per_page_calibration(self):
        """Test plan with multiple pages each having different calibration."""
        cal1 = CalibrationModel(
            pixels_per_meter=100.0,
            reference_point1=[0.0, 0.0],
            reference_point2=[100.0, 0.0],
            reference_distance_m=1.0,
        )
        cal2 = CalibrationModel(
            pixels_per_meter=200.0,
            reference_point1=[0.0, 0.0],
            reference_point2=[200.0, 0.0],
            reference_distance_m=1.0,
        )

        pages = [
            PageModel(source_path="floor1.pdf", page_index=0, floor=0, order=0, calibration=cal1),
            PageModel(source_path="floor2.pdf", page_index=0, floor=1, order=1, calibration=cal2),
        ]
        plan = PlanModel(pages=pages)

        sorted_pages = plan.get_sorted_pages()
        assert sorted_pages[0].calibration.pixels_per_meter == 100.0
        assert sorted_pages[1].calibration.pixels_per_meter == 200.0

    def test_plan_model_roundtrip_with_calibration(self):
        """Test full round-trip serialization with calibration."""
        cal = CalibrationModel(
            pixels_per_meter=150.5,
            verified=True,
            reference_point1=[10.0, 20.0],
            reference_point2=[160.5, 20.0],
            reference_distance_m=1.0,
        )
        page = PageModel(
            source_path="plan.pdf",
            page_index=0,
            rotation=180,
            floor=-1,
            order=2,
            calibration=cal,
        )
        plan = PlanModel(pages=[page], active_page_index=0)

        # Serialize
        json_data = plan.to_project_json()

        # Deserialize
        plan2 = PlanModel.from_project_json(json_data)

        assert plan2.pages[0].source_path == "plan.pdf"
        assert plan2.pages[0].rotation == 180
        assert plan2.pages[0].floor == -1
        assert plan2.pages[0].order == 2
        assert plan2.pages[0].calibration.pixels_per_meter == 150.5
        assert plan2.pages[0].calibration.verified is True
        assert plan2.pages[0].calibration.reference_point1 == [10.0, 20.0]


class TestPlanRenderer:
    """Tests for PlanRenderer with PyMuPDF display list caching and Pillow image loading."""

    def setup_method(self):
        """Create a test PDF for renderer tests."""
        import fitz

        self.doc = fitz.open()
        page = self.doc.new_page(width=612, height=792)
        page.draw_rect(fitz.Rect(50, 50, 200, 200), color=(1, 0, 0), fill=(1, 0, 0))
        page.insert_text((100, 300), "Renderer Test", fontsize=24, color=(0, 0, 0))

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.doc.save(self.temp_file.name)
        self.doc.close()
        self.pdf_path = self.temp_file.name

    def teardown_method(self):
        """Clean up test PDF."""
        if hasattr(self, "pdf_path") and Path(self.pdf_path).exists():
            Path(self.pdf_path).unlink()

    def test_plan_renderer_init(self):
        """Test PlanRenderer opens PDF document."""
        renderer = PlanRenderer(self.pdf_path)
        assert renderer.page_count() == 1
        renderer.close()

    def test_render_page_returns_qpixmap(self, qapp):
        """Test render_page returns a QPixmap."""
        from PySide6.QtGui import QPixmap

        renderer = PlanRenderer(self.pdf_path)
        try:
            pixmap = renderer.render_page(0, dpi=150)
            assert isinstance(pixmap, QPixmap)
            assert not pixmap.isNull()
            assert pixmap.width() > 0
            assert pixmap.height() > 0
        finally:
            renderer.close()

    def test_render_page_multiple_dpi(self, qapp):
        """Test render_page at different DPI levels produces different sizes."""
        renderer = PlanRenderer(self.pdf_path)
        try:
            pix_72 = renderer.render_page(0, dpi=72)
            pix_150 = renderer.render_page(0, dpi=150)
            pix_300 = renderer.render_page(0, dpi=300)

            # Higher DPI = larger pixmap
            assert pix_150.width() > pix_72.width()
            assert pix_300.width() > pix_150.width()
            assert pix_150.height() > pix_72.height()
            assert pix_300.height() > pix_150.height()
        finally:
            renderer.close()

    def test_display_list_cached(self):
        """Test display list is cached and reused on second call."""
        renderer = PlanRenderer(self.pdf_path)
        try:
            dlist1 = renderer.get_display_list(0)
            dlist2 = renderer.get_display_list(0)
            # Same object should be returned (cached)
            assert dlist1 is dlist2
            assert 0 in renderer._display_lists
        finally:
            renderer.close()

    def test_display_list_different_pages(self):
        """Test different pages get different display lists."""
        import fitz
        # Create multi-page PDF
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((50, 100), f"Page {i+1}", fontsize=24)
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        doc.save(tmp.name)
        doc.close()

        try:
            renderer = PlanRenderer(tmp.name)
            dlist0 = renderer.get_display_list(0)
            dlist1 = renderer.get_display_list(1)
            dlist2 = renderer.get_display_list(2)
            assert dlist0 is not dlist1
            assert dlist1 is not dlist2
            assert renderer.page_count() == 3
            renderer.close()
        finally:
            Path(tmp.name).unlink()

    def test_load_image_returns_qpixmap(self, qapp):
        """Test load_image returns QPixmap from PNG file."""
        from PySide6.QtGui import QPixmap
        from PIL import Image

        # Create test PNG
        img = Image.new("RGB", (200, 100), color=(255, 0, 0))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        tmp.close()

        try:
            renderer = PlanRenderer(self.pdf_path)
            pixmap = renderer.load_image(tmp.name)
            assert isinstance(pixmap, QPixmap)
            assert not pixmap.isNull()
            assert pixmap.width() == 200
            assert pixmap.height() == 100
            renderer.close()
        finally:
            Path(tmp.name).unlink()

    def test_load_image_exif_orientation(self, qapp):
        """Test load_image applies EXIF orientation correction."""
        from PIL import Image, ImageOps
        import io

        # Create image with EXIF orientation tag (rotate 90° CW)
        img = Image.new("RGB", (200, 100), color=(0, 255, 0))
        # Add EXIF data with orientation=6 (90° CW rotation)
        exif_data = img.getexif()
        exif_data[0x0112] = 6  # Orientation tag = 6 (90° CW)
        img.info["exif"] = exif_data.tobytes()

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img.save(tmp.name, exif=img.info.get("exif"))
        tmp.close()

        try:
            renderer = PlanRenderer(self.pdf_path)
            pixmap = renderer.load_image(tmp.name)
            # After EXIF rotation, width/height should be swapped
            # Original 200x100 with 90° rotation -> 100x200
            assert pixmap.width() == 100
            assert pixmap.height() == 200
            renderer.close()
        finally:
            Path(tmp.name).unlink()

    def test_close_releases_resources(self):
        """Test close() releases MuPDF resources."""
        renderer = PlanRenderer(self.pdf_path)
        # Populate display list cache
        renderer.get_display_list(0)
        assert len(renderer._display_lists) == 1

        renderer.close()
        assert len(renderer._display_lists) == 0

    def test_context_manager(self, qapp):
        """Test PlanRenderer works as context manager."""
        with PlanRenderer(self.pdf_path) as renderer:
            pixmap = renderer.render_page(0)
            assert not pixmap.isNull()
        # Should be closed after context exit
        assert len(renderer._display_lists) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])