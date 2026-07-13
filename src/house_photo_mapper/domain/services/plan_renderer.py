"""PlanRenderer: PyMuPDF rendering with display list caching, Pillow for images."""

import fitz  # PyMuPDF
from PIL import Image, ImageOps, ImageQt
from PySide6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import Dict, Optional
import logging

log = logging.getLogger(__name__)


class PlanRenderer:
    """Renders PDF pages and image files to QPixmap with caching.

    Uses PyMuPDF display lists for PDF rendering (10-50x speedup on re-renders).
    Uses Pillow with EXIF orientation correction for PNG/JPG/TIFF images.
    """

    def __init__(self, pdf_path: str):
        """Initialize renderer with a PDF document.

        Args:
            pdf_path: Path to PDF file.
        """
        self.pdf_path = pdf_path
        self._doc: fitz.Document = fitz.open(pdf_path)
        self._display_lists: Dict[int, fitz.DisplayList] = {}

    def get_display_list(self, page_num: int) -> fitz.DisplayList:
        """Get or create display list for a page.

        Display lists are cached to avoid re-parsing page content on every render.
        This provides 10-50x speedup for repeated renders at different zoom levels.

        Args:
            page_num: Page index in document.

        Returns:
            Cached or newly created DisplayList.
        """
        if page_num not in self._display_lists:
            page = self._doc[page_num]
            self._display_lists[page_num] = page.get_displaylist()
            log.debug(f"Created display list for page {page_num}")
        return self._display_lists[page_num]

    def render_page(self, page_num: int, dpi: float = 150) -> QPixmap:
        """Render a PDF page to QPixmap at specified DPI.

        Args:
            page_num: Page index in document.
            dpi: Target DPI (default 150). PDF base is 72 DPI.

        Returns:
            QPixmap with rendered page content.
        """
        dlist = self.get_display_list(page_num)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = dlist.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)

        # Zero-copy QImage from pixmap samples
        fmt = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        # CRITICAL: Keep pixmap alive while QImage references its buffer
        qimg._pymupdf_pixmap = pix

        return QPixmap.fromImage(qimg)

    def render_tile(
        self, page_num: int, dpi: float, clip_rect: fitz.Rect
    ) -> QPixmap:
        """Render a tile region of a PDF page for tile pyramid.

        Args:
            page_num: Page index in document.
            dpi: Target DPI for this tile level.
            clip_rect: Rectangle in page points to render.

        Returns:
            QPixmap with tile content.
        """
        dlist = self.get_display_list(page_num)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = dlist.get_pixmap(matrix=mat, clip=clip_rect, alpha=False, colorspace=fitz.csRGB)

        fmt = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        qimg._pymupdf_pixmap = pix
        return QPixmap.fromImage(qimg)

    def load_image(self, path: str) -> QPixmap:
        """Load PNG/JPG/TIFF image with EXIF orientation correction.

        Uses Pillow's ImageOps.exif_transpose to handle all 8 EXIF orientations.
        ImageQt provides zero-copy QImage conversion.

        Args:
            path: Path to image file.

        Returns:
            QPixmap with correctly oriented image.
        """
        with Image.open(path) as img:
            # Auto-rotate based on EXIF orientation tag (handles all 8 orientations)
            img = ImageOps.exif_transpose(img)

            # Convert to RGB/RGBA for ImageQt compatibility
            if img.mode not in ("RGB", "RGBA", "L", "1", "P"):
                img = img.convert("RGBA")

            # ImageQt.ImageQt subclasses QImage - zero-copy when possible
            qimg = ImageQt.ImageQt(img)
            return QPixmap.fromImage(qimg)

    def page_count(self) -> int:
        """Return number of pages in document."""
        return self._doc.page_count

    def close(self) -> None:
        """Release PyMuPDF resources.

        Clears display lists, closes document, and shrinks MuPDF store
        to release cached fonts/images/glyphs.
        """
        for dlist in self._display_lists.values():
            try:
                dlist.__del__()
            except Exception:
                pass
        self._display_lists.clear()
        self._doc.close()
        fitz.TOOLS.store_shrink(100)
        log.debug("PlanRenderer closed and resources released")

    def __enter__(self) -> "PlanRenderer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()