"""PlanSnippet: PyMuPDF plan region rendering for report generation."""

from __future__ import annotations

from dataclasses import dataclass

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


def extract_plan_snippet(
    pdf_path: str,
    page_index: int,
    center_x: float,
    center_y: float,
    radius_meters: float,
    pixels_per_meter: float,
    target_width_px: int = 400,
    target_height_px: int = 300,
) -> bytes:
    """Extract a plan region centered on the camera position as PNG bytes.

    Converts scene coordinates to PDF points, creates a clip rectangle,
    clamps to page bounds, and renders at appropriate zoom.

    Args:
        pdf_path: Path to the PDF file.
        page_index: Page index in the PDF document.
        center_x: Center X position in scene coordinates.
        center_y: Center Y position in scene coordinates.
        radius_meters: Radius of the visible region in meters.
        pixels_per_meter: Scale factor from scene coordinates to real-world meters.
        target_width_px: Target width in pixels for the output image.
        target_height_px: Target height in pixels for the output image.

    Returns:
        PNG bytes of the rendered plan region.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]

        # Convert scene coordinates to PDF points (72 DPI)
        pdf_center_x = (center_x / pixels_per_meter) * 72
        pdf_center_y = (center_y / pixels_per_meter) * 72
        radius_pts = radius_meters * 72

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
