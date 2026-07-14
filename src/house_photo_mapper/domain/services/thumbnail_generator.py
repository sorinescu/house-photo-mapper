"""Thumbnail generation service with background workers and caching."""

import hashlib
from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

from house_photo_mapper.infrastructure.qt_patterns import QtSafeRunnable


class ThumbnailSignals(QObject):
    """Signals for thumbnail worker."""

    thumbnail_ready = Signal(str, QPixmap)
    thumbnail_error = Signal(str, str)


class ThumbnailWorker(QtSafeRunnable):
    """Generate a single thumbnail in a background thread."""

    def __init__(
        self,
        path: str,
        target_size: tuple[int, int] = (200, 200),
        parent: QObject | None = None,
    ) -> None:
        """Initialize thumbnail worker.

        Args:
            path: Path to source image.
            target_size: Target thumbnail size (width, height).
            parent: Parent QObject.
        """
        super().__init__(parent)
        self.path = path
        self.target_size = target_size
        self.signals = ThumbnailSignals()

    @Slot()
    def run(self) -> None:
        """Generate thumbnail from source image."""
        try:
            with Image.open(self.path) as img:
                # Apply EXIF orientation
                img = ImageOps.exif_transpose(img)

                # Resize with high-quality resampling
                img.thumbnail(self.target_size, Image.Resampling.LANCZOS)

                # Convert to QImage
                if img.mode == "RGBA":
                    data = img.tobytes("raw", "RGBA")
                    qimage = QImage(
                        data,
                        img.width,
                        img.height,
                        QImage.Format.Format_RGBA8888,
                    )
                else:
                    data = img.tobytes("raw", "RGB")
                    qimage = QImage(
                        data,
                        img.width,
                        img.height,
                        QImage.Format.Format_RGB888,
                    )

                # Convert to QPixmap
                pixmap = QPixmap.fromImage(qimage)

                self.signals.thumbnail_ready.emit(self.path, pixmap)
        except Exception as e:
            self.signals.thumbnail_error.emit(self.path, str(e))


class ThumbnailGenerator(QObject):
    """Manage background thumbnail generation with LRU memory and disk cache.

    Features:
    - Background generation via QThreadPool
    - LRU memory cache (default 100MB)
    - Disk cache in .cache/thumbnails/
    - Cache invalidation based on source file mtime
    """

    thumbnail_ready = Signal(str, QPixmap)
    thumbnail_error = Signal(str, str)

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_cache_bytes: int = 100_000_000,
        parent: QObject | None = None,
    ) -> None:
        """Initialize thumbnail generator.

        Args:
            cache_dir: Directory for disk cache. None = no disk cache.
            max_cache_bytes: Maximum memory cache size in bytes.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._cache: dict[str, QPixmap] = {}
        self._cache_order: list[str] = []
        self._max_cache_bytes = max_cache_bytes
        self._current_cache_bytes = 0
        self._disk_cache_dir = cache_dir
        self._pending: set[str] = set()

        if self._disk_cache_dir:
            self._disk_cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, path: str) -> str:
        """Generate cache key from file path."""
        return hashlib.md5(path.encode()).hexdigest()

    def _estimate_pixmap_bytes(self, pixmap: QPixmap) -> int:
        """Estimate memory usage of a pixmap."""
        return pixmap.width() * pixmap.height() * 4  # RGBA

    def get_cached(self, path: str) -> QPixmap | None:
        """Get cached thumbnail if available.

        Args:
            path: Source image path.

        Returns:
            Cached QPixmap or None.
        """
        # Check memory cache
        if path in self._cache:
            # Move to end (most recently used)
            self._cache_order.remove(path)
            self._cache_order.append(path)
            return self._cache[path]

        # Check disk cache
        if self._disk_cache_dir:
            pixmap = self._load_from_disk(path)
            if pixmap:
                self._add_to_cache(path, pixmap)
                return pixmap

        return None

    def generate(self, path: str, target_size: tuple[int, int] = (200, 200)) -> None:
        """Queue thumbnail generation for a path.

        Args:
            path: Source image path.
            target_size: Target thumbnail size.
        """
        # Skip if already cached or pending
        if path in self._cache or path in self._pending:
            return

        self._pending.add(path)

        worker = ThumbnailWorker(path, target_size)
        worker.signals.thumbnail_ready.connect(self._on_thumbnail_ready)
        worker.signals.thumbnail_error.connect(self._on_thumbnail_error)

        QThreadPool.globalInstance().start(worker)

    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap) -> None:
        """Handle completed thumbnail generation."""
        self._pending.discard(path)
        self._add_to_cache(path, pixmap)

        if self._disk_cache_dir:
            self._save_to_disk(path, pixmap)

        self.thumbnail_ready.emit(path, pixmap)

    def _on_thumbnail_error(self, path: str, error: str) -> None:
        """Handle failed thumbnail generation."""
        self._pending.discard(path)
        self.thumbnail_error.emit(path, error)

    def _add_to_cache(self, path: str, pixmap: QPixmap) -> None:
        """Add pixmap to memory cache with LRU eviction."""
        # Evict if over limit
        pixmap_bytes = self._estimate_pixmap_bytes(pixmap)
        while (
            self._current_cache_bytes + pixmap_bytes > self._max_cache_bytes
            and self._cache_order
        ):
            self._evict_oldest()

        # Add to cache
        self._cache[path] = pixmap
        self._cache_order.append(path)
        self._current_cache_bytes += pixmap_bytes

    def _evict_oldest(self) -> None:
        """Remove oldest cached pixmap."""
        if not self._cache_order:
            return

        oldest_path = self._cache_order.pop(0)
        if oldest_path in self._cache:
            pixmap = self._cache.pop(oldest_path)
            self._current_cache_bytes -= self._estimate_pixmap_bytes(pixmap)

    def _load_from_disk(self, path: str) -> QPixmap | None:
        """Load thumbnail from disk cache.

        Args:
            path: Source image path.

        Returns:
            QPixmap from disk cache or None.
        """
        if not self._disk_cache_dir:
            return None

        cache_path = self._disk_cache_dir / f"{self._cache_key(path)}.png"
        if not cache_path.exists():
            return None

        # Check cache invalidation
        source_mtime = Path(path).stat().st_mtime
        cache_mtime = cache_path.stat().st_mtime
        if source_mtime > cache_mtime:
            return None

        pixmap = QPixmap(str(cache_path))
        return pixmap if not pixmap.isNull() else None

    def _save_to_disk(self, path: str, pixmap: QPixmap) -> None:
        """Save thumbnail to disk cache.

        Args:
            path: Source image path.
            pixmap: Thumbnail pixmap to save.
        """
        if not self._disk_cache_dir:
            return

        cache_path = self._disk_cache_dir / f"{self._cache_key(path)}.png"
        pixmap.save(str(cache_path), "PNG")

    def clear(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._cache_order.clear()
        self._current_cache_bytes = 0
        self._pending.clear()
