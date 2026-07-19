"""ReportGeneratorService — PDF report composition using ReportLab canvas API.

Creates professional PDF reports with one page per annotation containing:
- Header with page title and annotation subtitle
- Photo image (top portion)
- Plan snippet (from PlanSnippet service)
- Camera overlay (from CameraOverlay service)

Supports Unicode text via NotoSans font.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from house_photo_mapper.domain.services.camera_overlay import CameraOverlay
from house_photo_mapper.domain.services.plan_snippet import extract_plan_snippet, extract_full_plan_page


# Page size mapping
PAGE_SIZES: dict[str, tuple[float, float]] = {
    "A4 Portrait": A4,
    "A4 Landscape": landscape(A4),
    "US Letter": letter,
}

# Font registration
_FONTS_REGISTERED = False


def _register_fonts() -> None:
    """Register NotoSans fonts for Unicode text support."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    font_dir = Path(__file__).parent.parent.parent / "fonts"
    regular = font_dir / "NotoSans-Regular.ttf"
    bold = font_dir / "NotoSans-Bold.ttf"
    if regular.exists():
        pdfmetrics.registerFont(TTFont("NotoSans", str(regular)))
    if bold.exists():
        pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(bold)))
    _FONTS_REGISTERED = True


@dataclass(frozen=True)
class ReportPageData:
    """Data for a single page in the report.

    Attributes:
        annotation_id: Unique identifier for the annotation.
        photo_path: Absolute path to the photo file.
        plan_pdf_path: Path to the plan PDF file.
        plan_page_index: Page index in the plan PDF.
        plan_center_x: Center X position in scene coordinates.
        plan_center_y: Center Y position in scene coordinates.
        plan_pixels_per_meter: Scale factor from scene to real-world.
        direction_angle: Viewing direction in degrees (0=right, CCW).
        cone_angle: Cone spread angle in degrees.
        color: Hex color string for overlay.
        title: Annotation title (used as subtitle in header).
        page_title: Plan page title (used as header title).
        description: Free-text description.
        metadata: Dict with camera, lens, timestamp strings.
        floor: Floor number.
    """

    annotation_id: str
    photo_path: str
    plan_pdf_path: str
    plan_page_index: int
    plan_center_x: float
    plan_center_y: float
    plan_pixels_per_meter: float
    direction_angle: float
    cone_angle: float
    color: str
    title: str
    page_title: str = ""
    description: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
    floor: int = 0
    visible_area: list[list[float]] = field(default_factory=list)


class ReportGeneratorService:
    """Service for generating PDF reports with photos, plan snippets, and overlays.

    Uses ReportLab canvas API for fixed-page composition (not Platypus flowables).
    Each page contains: header, photo, plan snippet with camera overlay.
    """

    def __init__(self, project_dir: str) -> None:
        """Initialize the report generator.

        Args:
            project_dir: Path to the project root directory.
        """
        self.project_dir = Path(project_dir)
        _register_fonts()

    def generate(
        self,
        pages_data: list[ReportPageData],
        output_path: str,
        page_size: str = "A4 Portrait",
    ) -> str:
        """Generate a PDF report with one page per annotation.

        Args:
            pages_data: List of ReportPageData for each page.
            output_path: Path to write the output PDF.
            page_size: Page size string ("A4 Portrait", "A4 Landscape", "US Letter").

        Returns:
            The output_path string.
        """
        pagesize = PAGE_SIZES.get(page_size, A4)
        c = canvas.Canvas(output_path, pagesize=pagesize)

        for page_data in pages_data:
            self._render_page(c, page_data, pagesize)
            c.showPage()

        c.save()
        return output_path

    def _render_page(
        self,
        c: canvas.Canvas,
        page_data: ReportPageData,
        page_size: tuple[float, float],
    ) -> None:
        """Render a single page of the report.

        Layout (from top to bottom):
        - Header: page title (bold) + annotation subtitle
        - Photo with preserveAspectRatio
        - Plan snippet with camera overlay

        Args:
            c: ReportLab canvas to draw on.
            page_data: Data for this page.
            page_size: (width, height) in points.
        """
        width, height = page_size
        margin = 20 * 2.835  # 20mm in points

        # --- Header ---
        header_top = height - margin
        header_height = 30

        # Page title (bold)
        page_title = page_data.page_title or "Untitled Page"
        c.setFont("NotoSans-Bold", 14)
        c.drawString(margin, header_top - 16, page_title)

        # Annotation subtitle
        annotation_title = page_data.title or "Untitled"
        c.setFont("NotoSans", 10)
        c.drawString(margin, header_top - 30, annotation_title)

        # Separator line
        separator_y = header_top - header_height - 5
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.line(margin, separator_y, width - margin, separator_y)

        # --- Photo area: top 45% of remaining area ---
        content_top = separator_y - 10
        content_height = content_top - margin
        photo_height = content_height * 0.45
        photo_top = content_top
        photo_left = margin
        photo_width = width - 2 * margin

        try:
            img = ImageReader(page_data.photo_path)
            c.drawImage(
                img,
                photo_left,
                photo_top - photo_height,
                width=photo_width,
                height=photo_height,
                preserveAspectRatio=True,
                anchor="n",
            )
        except Exception:
            # If photo fails to load, draw a placeholder rectangle
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(photo_left, photo_top - photo_height, photo_width, photo_height)

        # --- Full plan page with annotation overlay ---
        plan_top = photo_top - photo_height - 10
        plan_height = plan_top - margin
        plan_width = photo_width

        try:
            # Render full plan page at high resolution for print quality
            plan_result = extract_full_plan_page(
                pdf_path=page_data.plan_pdf_path,
                page_index=page_data.plan_page_index,
                pixels_per_meter=page_data.plan_pixels_per_meter,
                target_width_px=max(int(plan_width), 1200),
                target_height_px=max(int(plan_height), 900),
                plan_area_width=plan_width,
                plan_area_height=plan_height,
            )
            plan_img = ImageReader(io.BytesIO(plan_result.image_bytes))
            plan_left = margin
            plan_bottom = plan_top - plan_height
            c.drawImage(
                plan_img,
                plan_left,
                plan_bottom,
                width=plan_width,
                height=plan_height,
                preserveAspectRatio=True,
                anchor="nw",
            )

            # Convert annotation scene coordinates to plan image pixels
            anno_x_in_plan = (page_data.plan_center_x - plan_result.offset_x) * plan_result.scale_x
            anno_y_in_plan = (page_data.plan_center_y - plan_result.offset_y) * plan_result.scale_y

            # Convert to PDF canvas coordinates (Y is flipped)
            canvas_x = plan_left + anno_x_in_plan
            canvas_y = plan_bottom + plan_height - anno_y_in_plan

            # Parse base color
            base_color = page_data.color[:7] if len(page_data.color) > 7 else page_data.color
            r, g, b = HexColor(base_color).red, HexColor(base_color).green, HexColor(base_color).blue

            # Draw camera marker (filled circle)
            c.saveState()
            c.setFillColorRGB(r, g, b)
            c.circle(canvas_x, canvas_y, 3, fill=1)
            c.restoreState()

            # Draw direction arrow
            c.saveState()
            rad = math.radians(page_data.direction_angle)
            dx = 10 * math.cos(rad)
            dy = -10 * math.sin(rad)
            c.setStrokeColorRGB(r, g, b)
            c.setLineWidth(2)
            c.line(canvas_x, canvas_y, canvas_x + dx, canvas_y + dy)
            c.restoreState()

            # Draw viewing cone (triangle)
            cone_length = 20.0
            left, right = CameraOverlay.compute_cone_vertices(
                canvas_x, canvas_y,
                page_data.direction_angle,
                page_data.cone_angle,
                cone_length,
            )
            left = (left[0], canvas_y - (left[1] - canvas_y))
            right = (right[0], canvas_y - (right[1] - canvas_y))

            c.saveState()
            c.setFillColorRGB(r, g, b, 0.1)
            c.setStrokeColorRGB(r, g, b, 0.6)
            c.setLineWidth(1)
            c.setDash(3, 2)
            path = c.beginPath()
            path.moveTo(canvas_x, canvas_y)
            path.lineTo(*left)
            path.lineTo(*right)
            path.close()
            c.drawPath(path, fill=1, stroke=1)
            c.restoreState()

            # Draw visible area rectangle
            if page_data.visible_area and len(page_data.visible_area) >= 1:
                rect_data = page_data.visible_area[0]
                if len(rect_data) >= 4:
                    rx, ry, rw, rh = rect_data[0], rect_data[1], rect_data[2], rect_data[3]
                    rect_x = plan_left + (rx - plan_result.offset_x) * plan_result.scale_x
                    rect_y = plan_bottom + plan_height - ((ry - plan_result.offset_y) * plan_result.scale_y) - rh * plan_result.scale_y
                    rect_w = rw * plan_result.scale_x
                    rect_h = rh * plan_result.scale_y

                    c.saveState()
                    c.setFillColorRGB(r, g, b, 0.12)
                    c.setStrokeColorRGB(r, g, b, 0.6)
                    c.setLineWidth(1.5)
                    c.setDash(6, 3)
                    c.rect(rect_x, rect_y, rect_w, rect_h, fill=1, stroke=1)
                    c.restoreState()

        except Exception:
            # If plan fails, draw a placeholder
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(margin, plan_top - plan_height, plan_width, plan_height)
