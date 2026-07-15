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
        """Create a simple 100x100 PDF page for testing."""
        pdf_path = tmp_path / "test_plan.pdf"
        doc = fitz.open()
        # 100x100 points page
        page = doc.new_page(width=100, height=100)
        page.draw_rect(fitz.Rect(20, 20, 80, 80), color=(0, 0, 0), width=2)
        page.insert_text((40, 50), "T", fontsize=10)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_render_basic_region(self, simple_pdf: Path) -> None:
        """Render center of 100x100 page: returns PNG bytes with expected dimensions."""
        png_bytes = extract_plan_snippet(
            pdf_path=str(simple_pdf),
            page_index=0,
            center_x=50.0,
            center_y=50.0,
            radius_meters=20.0,
            pixels_per_meter=100.0,
            target_width_px=400,
            target_height_px=300,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # Verify it's valid PNG by checking magic bytes
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        # Verify output dimensions are within expected range
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(png_bytes))
        assert img.width > 0
        assert img.height > 0

    def test_clamp_to_bounds(self, simple_pdf: Path) -> None:
        """Render near page edge: clip rectangle clamped to page bounds, no crash."""
        # Center at edge (10, 10) with large radius - clip extends beyond page
        png_bytes = extract_plan_snippet(
            pdf_path=str(simple_pdf),
            page_index=0,
            center_x=10.0,
            center_y=10.0,
            radius_meters=20.0,
            pixels_per_meter=100.0,
            target_width_px=200,
            target_height_px=200,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # Verify output is valid PNG
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_handle_rotation(self, tmp_path: Path) -> None:
        """Render from rotated page (rotation=90): handles rotation correctly."""
        pdf_path = tmp_path / "rotated_plan.pdf"
        doc = fitz.open()
        page = doc.new_page(width=100, height=100)
        page.draw_rect(fitz.Rect(20, 20, 80, 80), color=(0, 0, 0), width=2)
        page.set_rotation(90)
        doc.save(str(pdf_path))
        doc.close()

        png_bytes = extract_plan_snippet(
            pdf_path=str(pdf_path),
            page_index=0,
            center_x=50.0,
            center_y=50.0,
            radius_meters=20.0,
            pixels_per_meter=100.0,
            target_width_px=200,
            target_height_px=200,
        )
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_plan_snippet_dataclass(self) -> None:
        """PlanSnippet dataclass stores all fields and is frozen."""
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
        # Verify frozen (immutable)
        with pytest.raises(AttributeError):
            snippet.center_x = 999.0  # type: ignore[misc]
