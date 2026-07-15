"""Tests for ReportGeneratorService — PDF report creation with photo, plan, overlay."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.pdfgen import canvas

from house_photo_mapper.domain.services.report_generator import (
    ReportGeneratorService,
    ReportPageData,
)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a minimal JPEG image for testing."""
    img_path = tmp_path / "test_photo.jpg"
    img = Image.new("RGB", (640, 480), color=(100, 150, 200))
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal single-page PDF for testing."""
    pdf_path = tmp_path / "test_plan.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.drawString(100, 700, "Test Plan Page")
    c.save()
    return pdf_path


@pytest.fixture
def sample_pdf_3pages(tmp_path: Path) -> Path:
    """Create a 3-page PDF for testing."""
    pdf_path = tmp_path / "test_plan_3.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    for i in range(3):
        c.drawString(100, 700, f"Page {i + 1}")
        c.showPage()
    c.save()
    return pdf_path


@pytest.fixture
def output_pdf(tmp_path: Path) -> Path:
    """Output path for generated PDF."""
    return tmp_path / "output_report.pdf"


def _make_page_data(
    photo_path: str,
    plan_pdf_path: str,
    annotation_id: str = "ann-1",
    title: str = "Living Room",
    description: str = "Main living area",
    metadata: dict | None = None,
    floor: int = 0,
) -> ReportPageData:
    """Helper to create ReportPageData."""
    return ReportPageData(
        annotation_id=annotation_id,
        photo_path=photo_path,
        plan_pdf_path=plan_pdf_path,
        plan_page_index=0,
        plan_center_x=300.0,
        plan_center_y=400.0,
        plan_pixels_per_meter=100.0,
        direction_angle=45.0,
        cone_angle=60.0,
        color="#DC2828",
        title=title,
        description=description,
        metadata=metadata or {
            "camera_make": "Canon",
            "camera_model": "EOS R5",
            "lens_model": "RF 24-70mm",
            "timestamp": "2025-01-15 14:30",
        },
        floor=floor,
    )


class TestReportGeneratorService:
    """Tests for ReportGeneratorService."""

    def test_generate_creates_pdf(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """generate() with 1 page creates a valid PDF file."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [_make_page_data(str(sample_image), str(sample_pdf))]
        result = svc.generate(pages, str(output_pdf), "A4 Portrait")

        assert result == str(output_pdf)
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

        # Verify it's a valid PDF
        doc = fitz.open(str(output_pdf))
        assert len(doc) == 1
        doc.close()

    def test_generate_multiple_pages(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """generate() with 2 annotations creates PDF with 2 pages."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [
            _make_page_data(str(sample_image), str(sample_pdf), annotation_id="ann-1", title="Room 1"),
            _make_page_data(str(sample_image), str(sample_pdf), annotation_id="ann-2", title="Room 2"),
        ]
        svc.generate(pages, str(output_pdf), "A4 Portrait")

        doc = fitz.open(str(output_pdf))
        assert len(doc) == 2
        doc.close()

    def test_page_size_a4_portrait(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """A4 Portrait produces correct page dimensions (595.27 x 841.89 points)."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [_make_page_data(str(sample_image), str(sample_pdf))]
        svc.generate(pages, str(output_pdf), "A4 Portrait")

        doc = fitz.open(str(output_pdf))
        page = doc[0]
        width, height = page.rect.width, page.rect.height
        # A4 in points: 595.27 x 841.89
        assert width == pytest.approx(595.27, abs=1.0)
        assert height == pytest.approx(841.89, abs=1.0)
        doc.close()

    def test_page_size_a4_landscape(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """A4 Landscape produces landscape page dimensions."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [_make_page_data(str(sample_image), str(sample_pdf))]
        svc.generate(pages, str(output_pdf), "A4 Landscape")

        doc = fitz.open(str(output_pdf))
        page = doc[0]
        width, height = page.rect.width, page.rect.height
        # A4 landscape: height < width
        assert width > height
        assert width == pytest.approx(841.89, abs=1.0)
        assert height == pytest.approx(595.27, abs=1.0)
        doc.close()

    def test_page_size_us_letter(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """US Letter produces correct page dimensions (612 x 792 points)."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [_make_page_data(str(sample_image), str(sample_pdf))]
        svc.generate(pages, str(output_pdf), "US Letter")

        doc = fitz.open(str(output_pdf))
        page = doc[0]
        width, height = page.rect.width, page.rect.height
        assert width == pytest.approx(612.0, abs=1.0)
        assert height == pytest.approx(792.0, abs=1.0)
        doc.close()

    def test_figure_numbering(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """PDF text contains 'Figure 1', 'Figure 2' etc."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [
            _make_page_data(str(sample_image), str(sample_pdf), annotation_id="a1", title="First"),
            _make_page_data(str(sample_image), str(sample_pdf), annotation_id="a2", title="Second"),
        ]
        svc.generate(pages, str(output_pdf), "A4 Portrait")

        doc = fitz.open(str(output_pdf))
        for i, page in enumerate(doc):
            text = page.get_text()
            assert f"Figure {i + 1}" in text
        doc.close()

    def test_title_text_included(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """PDF text contains annotation title."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        pages = [_make_page_data(str(sample_image), str(sample_pdf), title="My Kitchen")]
        svc.generate(pages, str(output_pdf), "A4 Portrait")

        doc = fitz.open(str(output_pdf))
        text = doc[0].get_text()
        assert "My Kitchen" in text
        doc.close()

    def test_metadata_text_included(
        self,
        sample_image: Path,
        sample_pdf: Path,
        output_pdf: Path,
    ) -> None:
        """PDF text contains camera metadata."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        metadata = {
            "camera_make": "Canon",
            "camera_model": "EOS R5",
            "lens_model": "RF 24-70mm",
            "timestamp": "2025-01-15 14:30",
        }
        pages = [_make_page_data(str(sample_image), str(sample_pdf), metadata=metadata)]
        svc.generate(pages, str(output_pdf), "A4 Portrait")

        doc = fitz.open(str(output_pdf))
        text = doc[0].get_text()
        assert "Canon" in text
        assert "EOS R5" in text
        doc.close()

    def test_empty_annotations_creates_valid_pdf(
        self,
        sample_image: Path,
        output_pdf: Path,
    ) -> None:
        """generate() with empty list creates a valid empty PDF."""
        svc = ReportGeneratorService(project_dir=str(sample_image.parent))
        result = svc.generate([], str(output_pdf), "A4 Portrait")

        assert result == str(output_pdf)
        assert output_pdf.exists()
        # Empty list should produce 0 pages
        doc = fitz.open(str(output_pdf))
        assert len(doc) == 0
        doc.close()
