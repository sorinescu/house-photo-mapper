"""TilePyramid: Background tile generation via ProcessPoolExecutor for large PDFs."""

from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import fitz  # PyMuPDF
import logging

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TileSpec:
    """Specification for a single tile.

    Attributes:
        page_num: Page index in the PDF document.
        level: Zoom level index (0 = 72 DPI, 1 = 150 DPI, 2 = 300 DPI, 3 = 600 DPI).
        tile_x: Tile column index.
        tile_y: Tile row index.
        dpi: Target DPI for this tile.
    """

    page_num: int
    level: int
    tile_x: int
    tile_y: int
    dpi: float

    def __hash__(self) -> int:
        return hash((self.page_num, self.level, self.tile_x, self.tile_y))


# Constants
TILE_SIZE = 512
DPI_LEVELS = [72, 150, 300, 600]


def render_tile_worker(pdf_path: str, spec: TileSpec) -> bytes:
    """Worker function to render a single tile in a separate process.

    Opens its own document handle (PyMuPDF is not thread-safe).
    Returns PNG bytes for efficient caching.

    Args:
        pdf_path: Path to PDF file.
        spec: Tile specification.

    Returns:
        PNG bytes of the rendered tile.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[spec.page_num]
        zoom = spec.dpi / 72.0
        tile_pts = TILE_SIZE / zoom
        clip = fitz.Rect(
            spec.tile_x * tile_pts,
            spec.tile_y * tile_pts,
            (spec.tile_x + 1) * tile_pts,
            (spec.tile_y + 1) * tile_pts,
        )
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False, colorspace=fitz.csRGB)
        return pix.tobytes("png")
    finally:
        doc.close()
        fitz.TOOLS.store_shrink(100)


class TilePyramid:
    """Generates and caches PDF tiles at multiple DPI levels using ProcessPoolExecutor.

    Designed for large PDFs where rendering full pages at high DPI would block the UI.
    Tiles are generated on-demand in background processes and cached as PNG bytes.

    Attributes:
        pdf_path: Path to the PDF file.
        max_workers: Maximum number of worker processes (default 4).
    """

    def __init__(self, pdf_path: Path, max_workers: int = 4):
        """Initialize tile pyramid.

        Args:
            pdf_path: Path to PDF document.
            max_workers: Number of worker processes (default 4).
        """
        self.pdf_path = pdf_path
        self._executor = ProcessPoolExecutor(max_workers=max_workers, max_tasks_per_child=50)
        self._cache: Dict[TileSpec, bytes] = {}
        self._futures: Dict[TileSpec, Future] = {}

    def get_tile(self, spec: TileSpec) -> bytes:
        """Get tile PNG bytes, generating in background if not cached.

        Args:
            spec: Tile specification.

        Returns:
            PNG bytes of the tile.
        """
        if spec in self._cache:
            log.debug(f"Tile cache hit: {spec}")
            return self._cache[spec]

        # Check if already computing
        if spec in self._futures:
            future = self._futures[spec]
            result = future.result()
            self._cache[spec] = result
            del self._futures[spec]
            log.debug(f"Tile computed (was pending): {spec}")
            return result

        # Submit new task
        future = self._executor.submit(render_tile_worker, str(self.pdf_path), spec)
        self._futures[spec] = future
        log.debug(f"Tile submitted to worker: {spec}")

        # Block until result (in production, this could be async with callback)
        result = future.result()
        self._cache[spec] = result
        del self._futures[spec]
        log.debug(f"Tile completed and cached: {spec}")
        return result

    def get_tile_async(self, spec: TileSpec) -> Future:
        """Submit tile generation without blocking.

        Caller must handle the Future (e.g., add done callback).

        Args:
            spec: Tile specification.

        Returns:
            Future that will contain PNG bytes when complete.
        """
        if spec in self._cache:
            from concurrent.futures import Future as Fut
            f = Fut()
            f.set_result(self._cache[spec])
            return f

        if spec in self._futures:
            return self._futures[spec]

        future = self._executor.submit(render_tile_worker, str(self.pdf_path), spec)
        self._futures[spec] = future
        return future

    def get_tile_count(self, page_num: int, level: int) -> tuple[int, int]:
        """Calculate number of tiles needed for a page at a given level.

        Args:
            page_num: Page index.
            level: DPI level index.

        Returns:
            Tuple of (tiles_x, tiles_y).
        """
        doc = fitz.open(self.pdf_path)
        try:
            page = doc[page_num]
            dpi = DPI_LEVELS[level]
            zoom = dpi / 72.0
            page_width_pts = page.rect.width
            page_height_pts = page.rect.height
            tiles_x = max(1, int((page_width_pts * zoom + TILE_SIZE - 1) // TILE_SIZE))
            tiles_y = max(1, int((page_height_pts * zoom + TILE_SIZE - 1) // TILE_SIZE))
            return tiles_x, tiles_y
        finally:
            doc.close()

    def shutdown(self) -> None:
        """Shutdown executor and release resources."""
        self._executor.shutdown(wait=True)
        self._cache.clear()
        self._futures.clear()
        log.debug("TilePyramid shutdown complete")

    def __enter__(self) -> "TilePyramid":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()


if __name__ == "__main__":
    # Quick manual test
    import tempfile
    from pathlib import Path

    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(0, 0, 612, 792), color=(0, 0, 0), width=2)
    page.insert_text((100, 100), "Test PDF for TilePyramid", fontsize=24)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        doc.save(f.name)
        doc.close()

        pdf_path = Path(f.name)
        try:
            pyramid = TilePyramid(pdf_path, max_workers=2)
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
            png_bytes = pyramid.get_tile(spec)
            print(f"Generated tile: {len(png_bytes)} bytes")
            pyramid.shutdown()
        finally:
            pdf_path.unlink()