"""Tests for TilePyramid and TileSpec."""

import pytest
from pathlib import Path
import tempfile
import fitz

from house_photo_mapper.domain.services.tile_pyramid import (
    TileSpec,
    TilePyramid,
    render_tile_worker,
    TILE_SIZE,
    DPI_LEVELS,
)


class TestTileSpec:
    """Tests for TileSpec dataclass."""

    def test_tile_spec_creation(self):
        """Test TileSpec creation with all fields."""
        spec = TileSpec(page_num=0, level=1, tile_x=2, tile_y=3, dpi=150)
        assert spec.page_num == 0
        assert spec.level == 1
        assert spec.tile_x == 2
        assert spec.tile_y == 3
        assert spec.dpi == 150

    def test_tile_spec_hashable(self):
        """Test TileSpec can be used as dict key."""
        spec1 = TileSpec(page_num=0, level=1, tile_x=0, tile_y=0, dpi=150)
        spec2 = TileSpec(page_num=0, level=1, tile_x=0, tile_y=0, dpi=150)
        spec3 = TileSpec(page_num=0, level=2, tile_x=0, tile_y=0, dpi=300)

        cache = {spec1: "tile_data"}
        assert spec2 in cache  # Equal specs should have same hash
        assert spec3 not in cache  # Different level should have different hash

    def test_tile_spec_equality(self):
        """Test TileSpec equality."""
        spec1 = TileSpec(page_num=1, level=0, tile_x=5, tile_y=5, dpi=72)
        spec2 = TileSpec(page_num=1, level=0, tile_x=5, tile_y=5, dpi=72)
        spec3 = TileSpec(page_num=1, level=1, tile_x=5, tile_y=5, dpi=150)

        assert spec1 == spec2
        assert spec1 != spec3


class TestConstants:
    """Tests for module constants."""

    def test_tile_size(self):
        """Test TILE_SIZE constant."""
        assert TILE_SIZE == 512

    def test_dpi_levels(self):
        """Test DPI_LEVELS constant."""
        assert DPI_LEVELS == [72, 150, 300, 600]


class TestRenderTileWorker:
    """Tests for render_tile_worker function."""

    def test_render_tile_worker_returns_png_bytes(self):
        """Test worker returns valid PNG bytes."""
        # Create a test PDF
        doc = fitz.open()
        page = doc.new_page()
        page.draw_rect(fitz.Rect(0, 0, 612, 792), color=(1, 0, 0), fill=(1, 0, 0))
        page.insert_text((100, 100), "Test", fontsize=24, color=(0, 1, 0))

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc.save(f.name)
            doc.close()

            try:
                spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
                png_bytes = render_tile_worker(f.name, spec)

                # Verify it's PNG data
                assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
                assert len(png_bytes) > 100  # Should have some content
            finally:
                Path(f.name).unlink()


class TestTilePyramid:
    """Tests for TilePyramid class."""

    def setup_method(self):
        """Create a test PDF for each test."""
        self.doc = fitz.open()
        page = self.doc.new_page()
        page.draw_rect(fitz.Rect(0, 0, 612, 792), color=(0, 0, 1), fill=(0.9, 0.9, 1))
        page.insert_text((50, 100), "TilePyramid Test", fontsize=36, color=(0, 0, 0))
        page.draw_rect(fitz.Rect(100, 200, 300, 400), color=(1, 0, 0), width=3)

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.doc.save(self.temp_file.name)
        self.doc.close()
        self.pdf_path = Path(self.temp_file.name)

    def teardown_method(self):
        """Clean up test PDF and pyramid."""
        if hasattr(self, "pdf_path") and self.pdf_path.exists():
            self.pdf_path.unlink()

    def test_tile_pyramid_init(self):
        """Test TilePyramid initialization."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        assert pyramid.pdf_path == self.pdf_path
        pyramid.shutdown()

    def test_get_tile_returns_png_bytes(self):
        """Test get_tile returns PNG bytes."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
            png_bytes = pyramid.get_tile(spec)

            assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
            assert len(png_bytes) > 100
        finally:
            pyramid.shutdown()

    def test_get_tile_caching(self):
        """Test tile caching works."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)

            # First call - generates tile
            png1 = pyramid.get_tile(spec)
            assert spec in pyramid._cache

            # Second call - should return cached
            png2 = pyramid.get_tile(spec)
            assert png1 == png2
            assert len(pyramid._cache) == 1
        finally:
            pyramid.shutdown()

    def test_get_tile_different_levels(self):
        """Test tiles at different DPI levels."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            for level, dpi in enumerate(DPI_LEVELS):
                spec = TileSpec(page_num=0, level=level, tile_x=0, tile_y=0, dpi=dpi)
                png_bytes = pyramid.get_tile(spec)
                assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
                assert len(png_bytes) > 0
        finally:
            pyramid.shutdown()

    def test_get_tile_multiple_tiles(self):
        """Test generating multiple tiles for same page."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            tiles = []
            for tx in range(2):
                for ty in range(2):
                    spec = TileSpec(page_num=0, level=0, tile_x=tx, tile_y=ty, dpi=72)
                    png = pyramid.get_tile(spec)
                    tiles.append(png)

            assert len(tiles) == 4
            assert len(pyramid._cache) == 4
        finally:
            pyramid.shutdown()

    def test_get_tile_count(self):
        """Test get_tile_count returns correct tile grid size."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            tiles_x, tiles_y = pyramid.get_tile_count(0, 0)  # Level 0 = 72 DPI
            assert tiles_x >= 1
            assert tiles_y >= 1

            # Higher DPI = more tiles
            tiles_x_1, tiles_y_1 = pyramid.get_tile_count(0, 1)  # Level 1 = 150 DPI
            tiles_x_2, tiles_y_2 = pyramid.get_tile_count(0, 2)  # Level 2 = 300 DPI

            assert tiles_x_1 >= tiles_x
            assert tiles_y_1 >= tiles_y
            assert tiles_x_2 >= tiles_x_1
            assert tiles_y_2 >= tiles_y_1
        finally:
            pyramid.shutdown()

    def test_get_tile_async_returns_future(self):
        """Test get_tile_async returns a Future."""
        from concurrent.futures import Future

        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
            future = pyramid.get_tile_async(spec)
            assert isinstance(future, Future)

            # Result should be available
            png_bytes = future.result()
            assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        finally:
            pyramid.shutdown()

    def test_get_tile_async_cached(self):
        """Test get_tile_async returns completed future for cached tile."""
        from concurrent.futures import Future

        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        try:
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)

            # Populate cache first
            pyramid.get_tile(spec)

            # Async should return completed future
            future = pyramid.get_tile_async(spec)
            assert future.done()
            assert future.result() == pyramid._cache[spec]
        finally:
            pyramid.shutdown()

    def test_context_manager(self):
        """Test TilePyramid as context manager."""
        with TilePyramid(self.pdf_path, max_workers=2) as pyramid:
            spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
            png = pyramid.get_tile(spec)
            assert png[:8] == b"\x89PNG\r\n\x1a\n"
        # Should be shut down after context

    def test_shutdown_clears_resources(self):
        """Test shutdown clears cache and futures."""
        pyramid = TilePyramid(self.pdf_path, max_workers=2)
        spec = TileSpec(page_num=0, level=0, tile_x=0, tile_y=0, dpi=72)
        pyramid.get_tile(spec)

        assert len(pyramid._cache) == 1
        pyramid.shutdown()
        assert len(pyramid._cache) == 0
        assert len(pyramid._futures) == 0


class TestTilePyramidIntegration:
    """Integration tests for TilePyramid with real PDF."""

    def test_multi_page_pdf(self):
        """Test TilePyramid with multi-page PDF."""
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((50, 100), f"Page {i+1}", fontsize=36)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc.save(f.name)
            doc.close()

            pdf_path = Path(f.name)
            try:
                with TilePyramid(pdf_path, max_workers=2) as pyramid:
                    # Test all pages
                    for page_num in range(3):
                        spec = TileSpec(page_num=page_num, level=0, tile_x=0, tile_y=0, dpi=72)
                        png = pyramid.get_tile(spec)
                        assert png[:8] == b"\x89PNG\r\n\x1a\n"
            finally:
                pdf_path.unlink()

    @pytest.mark.slow
    def test_high_dpi_tiles(self):
        """Test tile generation at highest DPI level (600)."""
        doc = fitz.open()
        page = doc.new_page()
        # Add more content to generate larger PNG
        for i in range(10):
            page.draw_rect(fitz.Rect(i*50, i*50, i*50+100, i*50+100), color=(0, 0, 0), width=2)
            page.insert_text((i*50+10, i*50+10), f"Tile {i}", fontsize=16)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc.save(f.name)
            doc.close()

            pdf_path = Path(f.name)
            try:
                with TilePyramid(pdf_path, max_workers=2) as pyramid:
                    spec = TileSpec(page_num=0, level=3, tile_x=0, tile_y=0, dpi=600)
                    png = pyramid.get_tile(spec)
                    assert png[:8] == b"\x89PNG\r\n\x1a\n"
                    # At 600 DPI with more content, tile should be larger
                    assert len(png) > 5000
            finally:
                pdf_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])