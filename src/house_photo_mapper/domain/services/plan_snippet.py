"""PlanSnippet: PyMuPDF plan region rendering for report generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import fitz  # PyMuPDF


@dataclass(frozen=True)
class PlanSnippet:
    """Data class storing plan snippet extraction parameters.

    Attributes:
        pdf_path: Path to the PDF file.
        page_index: Page index in the PDF document.
        center_x: Center X position in scene coordinates.
        center_y: Center Y position in scene coordinates.
        radius_meters: Radius of the visible region in meters.
        pixels_per_meter: Scale factor from scene coordinates to real-world meters.
    """

    pdf_path: str
    page_index: int
    center_x: float
    center_y: float
    radius_meters: float
    pixels_per_meter: float


class FullPlanResult(NamedTuple):
    """Result of full plan page extraction."""

    image_bytes: bytes
    scale_x: float  # pixels per scene unit in the rendered image
    scale_y: float
    offset_x: float  # scene X coordinate of image left edge
    offset_y: float  # scene Y coordinate of image top edge


def extract_full_plan_page(
    pdf_path: str,
    page_index: int,
    pixels_per_meter: float,
    target_width_px: int = 800,
    target_height_px: int = 600,
    render_dpi: float = 150.0,
    plan_area_width: float | None = None,
    plan_area_height: float | None = None,
) -> FullPlanResult:
    """Extract the full plan page as PNG bytes with coordinate mapping info.

    Renders the entire page scaled to fit the target dimensions, and returns
    scale factors needed to convert scene coordinates to image pixel coordinates.

    Args:
        pdf_path: Path to the PDF file.
        page_index: Page index in the PDF document.
        pixels_per_meter: Scale factor from real-world meters to scene pixels.
        target_width_px: Target width in pixels for the output image.
        target_height_px: Target height in pixels for the output image.
        render_dpi: DPI at which scene coordinates are defined (matches app, default 150).
        plan_area_width: Width of the plan area on the PDF canvas (points).
        plan_area_height: Height of the plan area on the PDF canvas (points).

    Returns:
        FullPlanResult with image bytes and coordinate mapping info.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        page_rect = page.rect

        # Calculate zoom to fit target dimensions
        zoom_x = target_width_px / page_rect.width
        zoom_y = target_height_px / page_rect.height
        zoom = min(zoom_x, zoom_y)

        # Render full page
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        image_bytes = pix.tobytes("png")

        # Scale factor from scene pixels to image pixels:
        # image_pixels = scene_pixels * 72 * zoom / render_dpi
        img_scale = 72.0 * zoom / render_dpi

        # When the image is drawn with preserveAspectRatio into the plan area,
        # there's an additional drawing scale:
        # drawing_scale = min(plan_area_width / img_width, plan_area_height / img_height)
        if plan_area_width is not None and plan_area_height is not None:
            drawing_scale = min(plan_area_width / pix.width, plan_area_height / pix.height)
        else:
            drawing_scale = 1.0

        # Combined scale: scene pixels -> image pixels -> plan area pixels
        scale_x = img_scale * drawing_scale
        scale_y = img_scale * drawing_scale

        # Offset: scene coordinate of image (0,0) = top-left corner
        offset_x = 0.0
        offset_y = 0.0

        return FullPlanResult(
            image_bytes=image_bytes,
            scale_x=scale_x,
            scale_y=scale_y,
            offset_x=offset_x,
            offset_y=offset_y,
        )
    finally:
        doc.close()
        fitz.TOOLS.store_shrink(100)


def extract_plan_snippet(
    pdf_path: str,
    page_index: int,
    center_x: float,
    center_y: float,
    radius_meters: float,
    pixels_per_meter: float,
    target_width_px: int = 400,
    target_height_px: int = 300,
    render_dpi: float = 150.0,
) -> bytes:
    """Extract a plan region centered on the camera position as PNG bytes.

    Converts scene coordinates to PDF points, creates a clip rectangle,
    clamps to page bounds, and renders at appropriate zoom.

    Args:
        pdf_path: Path to the PDF file.
        page_index: Page index in the PDF document.
        center_x: Center X position in scene coordinates (pixels at render_dpi).
        center_y: Center Y position in scene coordinates (pixels at render_dpi).
        radius_meters: Radius of the visible region in meters.
        pixels_per_meter: Scale factor from real-world meters to scene pixels.
        target_width_px: Target width in pixels for the output image.
        target_height_px: Target height in pixels for the output image.
        render_dpi: DPI at which scene coordinates are defined (matches app, default 150).

    Returns:
        PNG bytes of the rendered plan region.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]

        # Convert scene coordinates (pixels at render_dpi) to PDF points (72 DPI)
        # scene_pixels = pdf_points * (render_dpi / 72)
        # => pdf_points = scene_pixels * 72 / render_dpi
        pdf_center_x = center_x * 72.0 / render_dpi
        pdf_center_y = center_y * 72.0 / render_dpi
        radius_pts = radius_meters * pixels_per_meter * 72.0 / render_dpi

        # Create clip rectangle
        clip = fitz.Rect(
            pdf_center_x - radius_pts,
            pdf_center_y - radius_pts,
            pdf_center_x + radius_pts,
            pdf_center_y + radius_pts,
        )

        # Clamp to page bounds
        # PyMuPDF handles rotation internally — page.rect is always the
        # unrotated media box. For rotated pages, skip clipping and render
        # the full page; PyMuPDF rotates the output automatically.
        if page.rotation == 0:
            clip = clip & page.rect
            # Ensure clip has non-zero dimensions
            if clip.width <= 0 or clip.height <= 0:
                clip = fitz.Rect(0, 0, min(target_width_px, page.rect.width),
                                 min(target_height_px, page.rect.height))
        else:
            # For rotated pages, render the full visible area
            clip = page.rect

        # Calculate zoom to fit target dimensions
        zoom_x = target_width_px / clip.width
        zoom_y = target_height_px / clip.height
        zoom = min(zoom_x, zoom_y)

        # Render
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()
        fitz.TOOLS.store_shrink(100)
