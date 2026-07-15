"""Memory usage profiling and optimization utilities.

Provides memory monitoring, lazy loading helpers for annotation graphics,
and memory cache size limits with warning logging.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB.

    Uses resource module on Unix, falls back to psutil if available.

    Returns:
        Memory usage in megabytes, or 0.0 if unavailable.
    """
    try:
        import resource

        # ru_maxrss is in bytes on macOS, KB on Linux
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)  # bytes to MB
        else:
            return usage / 1024  # KB to MB
    except ImportError:
        pass

    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except (ImportError, Exception):
        return 0.0


def get_current_rss_mb() -> float:
    """Get current RSS (Resident Set Size) in MB.

    Returns:
        Current RSS in megabytes, or 0.0 if unavailable.
    """
    try:
        import resource

        # On macOS, getrusage returns current ru_maxrss (peak),
        # but we can try /proc/self/status on Linux
        if sys.platform == "linux":
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024  # KB to MB
        # Fallback to maxrss (peak) on macOS
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)
        return usage / 1024
    except (ImportError, OSError):
        return 0.0


class MemoryMonitor:
    """Monitor memory usage and log warnings for high consumption.

    Tracks memory usage over time and provides warnings when
    usage exceeds configurable thresholds.

    Features:
    - Periodic memory sampling in background thread
    - Configurable warning thresholds
    - Memory usage history for profiling
    - Integration with benchmark harness
    """

    def __init__(
        self,
        warning_threshold_mb: float = 1024.0,
        critical_threshold_mb: float = 2048.0,
        sample_interval_s: float = 5.0,
    ) -> None:
        """Initialize memory monitor.

        Args:
            warning_threshold_mb: Log warning when memory exceeds this (MB).
            critical_threshold_mb: Log critical when memory exceeds this (MB).
            sample_interval_s: Interval between background samples.
        """
        self._warning_threshold_mb = warning_threshold_mb
        self._critical_threshold_mb = critical_threshold_mb
        self._sample_interval_s = sample_interval_s

        self._samples: list[tuple[float, float]] = []  # (timestamp, mb)
        self._monitoring = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def check_memory(self) -> dict[str, float]:
        """Check current memory usage and log warnings if needed.

        Returns:
            Dict with current_mb and peak_mb.
        """
        current_mb = get_current_rss_mb()
        peak_mb = get_memory_usage_mb()

        with self._lock:
            self._samples.append((time.time(), current_mb))

        if current_mb > self._critical_threshold_mb:
            logger.critical(
                "memory_critical current_mb=%.1f threshold_mb=%.1f",
                current_mb,
                self._critical_threshold_mb,
            )
        elif current_mb > self._warning_threshold_mb:
            logger.warning(
                "memory_warning current_mb=%.1f threshold_mb=%.1f",
                current_mb,
                self._warning_threshold_mb,
            )

        return {"current_mb": current_mb, "peak_mb": peak_mb}

    def start_monitoring(self) -> None:
        """Start background memory monitoring thread."""
        if self._monitoring:
            return

        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=self._sample_interval_s * 2)
            self._thread = None

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            self.check_memory()
            time.sleep(self._sample_interval_s)

    def get_samples(self) -> list[tuple[float, float]]:
        """Get recorded memory samples.

        Returns:
            List of (timestamp, memory_mb) tuples.
        """
        with self._lock:
            return list(self._samples)

    def get_stats(self) -> dict[str, float]:
        """Get memory usage statistics.

        Returns:
            Dict with min_mb, max_mb, mean_mb, sample_count.
        """
        with self._lock:
            if not self._samples:
                return {"min_mb": 0, "max_mb": 0, "mean_mb": 0, "sample_count": 0}
            mb_values = [s[1] for s in self._samples]
            return {
                "min_mb": min(mb_values),
                "max_mb": max(mb_values),
                "mean_mb": sum(mb_values) / len(mb_values),
                "sample_count": len(mb_values),
            }

    def clear(self) -> None:
        """Clear recorded samples."""
        with self._lock:
            self._samples.clear()


class MemoryCache:
    """A cache with memory size limits and LRU eviction.

    Tracks the memory footprint of cached items and evicts
    oldest entries when the size limit is exceeded.

    Features:
    - Configurable memory limit in bytes
    - LRU eviction policy
    - Memory usage tracking
    - Size estimation per item
    """

    def __init__(
        self,
        max_bytes: int = 500_000_000,  # 500MB default
        estimator: Callable[[Any], int] | None = None,
    ) -> None:
        """Initialize memory cache.

        Args:
            max_bytes: Maximum cache size in bytes.
            estimator: Function to estimate item size in bytes.
                      Defaults to sys.getsizeof.
        """
        self._max_bytes = max_bytes
        self._current_bytes = 0
        self._cache: dict[str, Any] = {}
        self._order: list[str] = []  # LRU order (oldest first)
        self._estimator = estimator or sys.getsizeof

    def get(self, key: str) -> Any | None:
        """Get item from cache, updating LRU order.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """Add item to cache with LRU eviction.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        # Remove existing entry if updating
        if key in self._cache:
            old_value = self._cache[key]
            self._current_bytes -= self._estimator(old_value)
            self._order.remove(key)

        # Estimate size of new item
        item_bytes = self._estimator(value)

        # Evict until we have room
        while (
            self._current_bytes + item_bytes > self._max_bytes
            and self._order
        ):
            self._evict_oldest()

        # Add to cache
        self._cache[key] = value
        self._order.append(key)
        self._current_bytes += item_bytes

    def _evict_oldest(self) -> None:
        """Remove the oldest (least recently used) item."""
        if not self._order:
            return

        oldest_key = self._order.pop(0)
        if oldest_key in self._cache:
            value = self._cache.pop(oldest_key)
            self._current_bytes -= self._estimator(value)

    def remove(self, key: str) -> bool:
        """Remove an item from the cache.

        Args:
            key: Cache key.

        Returns:
            True if the item was found and removed.
        """
        if key in self._cache:
            value = self._cache.pop(key)
            self._current_bytes -= self._estimator(value)
            self._order.remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._order.clear()
        self._current_bytes = 0

    @property
    def size_bytes(self) -> int:
        """Current cache size in bytes."""
        return self._current_bytes

    @property
    def max_bytes(self) -> int:
        """Maximum cache size in bytes."""
        return self._max_bytes

    @property
    def count(self) -> int:
        """Number of items in cache."""
        return len(self._cache)

    @property
    def utilization(self) -> float:
        """Cache utilization as a fraction (0.0 to 1.0)."""
        if self._max_bytes == 0:
            return 0.0
        return self._current_bytes / self._max_bytes

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with count, size_bytes, max_bytes, utilization.
        """
        return {
            "count": self.count,
            "size_bytes": self.size_bytes,
            "max_bytes": self.max_bytes,
            "utilization": round(self.utilization, 4),
        }


@contextmanager
def memory_tracked(
    label: str,
    monitor: MemoryMonitor | None = None,
    *,
    log_usage: bool = True,
):  # type: ignore[return]
    """Context manager that tracks memory usage for a block.

    Usage:
        with memory_tracked("load_project"):
            load_large_project(...)

    Args:
        label: Label for the memory tracking block.
        monitor: MemoryMonitor to use. None = creates temporary check.
        log_usage: Whether to log memory usage at exit.
    """
    start_mb = get_current_rss_mb()
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_mb = get_current_rss_mb()
        duration_ms = (time.perf_counter() - start_time) * 1000
        delta_mb = end_mb - start_mb

        if log_usage:
            logger.info(
                "memory_tracked label=%s delta_mb=%.1f duration_ms=%.1f end_mb=%.1f",
                label,
                delta_mb,
                duration_ms,
                end_mb,
            )

        if monitor:
            monitor.check_memory()


def estimate_pixmap_bytes(width: int, height: int, depth: int = 4) -> int:
    """Estimate memory usage of a pixmap in bytes.

    Args:
        width: Pixmap width in pixels.
        height: Pixmap height in pixels.
        depth: Bytes per pixel (4 for RGBA, 3 for RGB).

    Returns:
        Estimated memory usage in bytes.
    """
    return width * height * depth


def estimate_annotation_group_bytes(count: int) -> int:
    """Estimate memory usage for a group of annotation graphics.

    Each annotation group contains ~5 QGraphicsItems with
    associated geometry and style data.

    Args:
        count: Number of annotation groups.

    Returns:
        Estimated memory usage in bytes.
    """
    # Rough estimate: ~2KB per annotation group (marker + arrow + cone + area + group)
    return count * 2048
