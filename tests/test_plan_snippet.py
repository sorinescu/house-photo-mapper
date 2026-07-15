"""Tests for PlanSnippet service."""

import tempfile
from pathlib import Path

import fitz
import pytest

from house_photo_mapper.domain.services.plan_snippet import (
    PlanSnippet,
    extract_plan_snippet,
)


class TestPlanSnippet:
    """Tests for PlanSnippet dataclass and extract_plan_snippet function."""

    @pytest.fixture
    def simple_pdf(self, tmp_path: Path) -> Path:
        """Create a simple PDF with a known rectangle for testing."""
        pdf_path = tmp_path / "test_plan.pdf"
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size in points
        # Draw a rectangle in the center
        page.draw_rect(fitz.Rect(200, 300, 400, 500), color=(0, 0, 0), width=2)
        page.insert_text((250, 400), "Test Plan", fontsize=16)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_render_basic_region(self, simple_pdf: Path) -> None:
        """Test rendering a basic region from center of page."""
        png_bytes = extract_plan_snippet(
            pdf_path=str(simple_pdf),
            page_index=0,
            center_x=297.5,
            center_y=421.0,
            radius_meters=5.0,
            pixels_per_meter=72 / 2.835,  # ~25.4 pixels per meter (1 inch = 2.835pt)
            target_width_px=400,
            target_height_px=300,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # Verify it's valid PNG by checking magic bytes
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_clamp_to_bounds(self, simple_pdf: Path) -> None:
        """Test rendering near page edge clamps correctly without crash."""
        png_bytes = extract_plan_snippet(
            pdf_path=str(simple_pdf),
            page_index=0,
            center_x=10.0,
            center_y=10.0,
            radius_meters=5.0,
            pixels_per_meter=72 / 2.835,
            target_width_px=200,
            target_height_px=200,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

    def test_handle_rotation(self, tmp_path: Path) -> None:
        """Test rendering from a rotated page."""
        pdf_path = tmp_path / "rotated_plan.pdf"
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(100, 100, 400, 400), color=(0, 0, 0), width=2)
        # Set rotation
        page.set_rotation(90)
        doc.save(str(pdf_path))
        doc.close()

        png_bytes = extract_plan_snippet(
            pdf_path=str(pdf_path),
            page_index=0,
            center_x=297.5,
            center_y=421.0,
            radius_meters=5.0,
            pixels_per_meter=72 / 2.835,
            target_width_px=400,
            target_height_px=300,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

    def test_plan_snippet_dataclass(self) -> None:
        """Test PlanSnippet dataclass stores all fields correctly."""
        snippet = PlanSnippet(
            pdf_path="/path/to/plan.pdf",
            page_index=0,
            center_x=100.0,
            center_y=200.0,
            radius_meters=5.0,
            pixels_per_meter=72.0,
        )
        assert snippet.pdf_path == "/path/to/plan.pdf"
        assert snippet.page_index == 0
        assert snippet.center_x == 100.0
        assert snippet.center_y == 200.0
        assert snippet.radius_meters == 5.0
        assert snippet.pixels_per_meter == 72.0
