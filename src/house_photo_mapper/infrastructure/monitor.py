"""Performance monitoring for tracking operation times and logging warnings.

Integrates with the benchmark harness to provide real-time monitoring
of viewport interactions, save/load operations, and thumbnail generation.
Logs warnings when operations exceed the 100ms threshold.
"""

from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from typing import Any

from house_photo_mapper.infrastructure.benchmark import PerformanceBenchmark, get_benchmark
from house_photo_mapper.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Default warning threshold in milliseconds
DEFAULT_WARNING_THRESHOLD_MS = 100.0


class PerformanceMonitor:
    """Track operation durations and log warnings for slow operations.

    Provides rolling window statistics for recent operations and
    integrates with the benchmark harness for persistent logging.

    Features:
    - Rolling window of recent durations (default: last 100)
    - Warning logging for operations exceeding threshold
    - Per-operation statistics (mean, min, max, p95)
    - Integration with PerformanceBenchmark for persistent metrics
    """

    def __init__(
        self,
        warning_threshold_ms: float = DEFAULT_WARNING_THRESHOLD_MS,
        window_size: int = 100,
        benchmark: PerformanceBenchmark | None = None,
    ) -> None:
        """Initialize performance monitor.

        Args:
            warning_threshold_ms: Log warning when operation exceeds this (ms).
            window_size: Number of recent operations to keep in rolling window.
            benchmark: Benchmark instance for persistent logging. None = global.
        """
        self._warning_threshold_ms = warning_threshold_ms
        self._window_size = window_size
        self._benchmark = benchmark

        # Rolling windows per operation type
        self._windows: dict[str, deque[float]] = {}
        self._total_counts: dict[str, int] = {}
        self._total_times: dict[str, float] = {}

    def _get_benchmark(self) -> PerformanceBenchmark:
        """Get benchmark instance (lazy init)."""
        if self._benchmark is None:
            self._benchmark = get_benchmark()
        return self._benchmark

    @contextmanager
    def track(
        self,
        operation: str,
        *,
        warn_threshold_ms: float | None = None,
        **extra: Any,
    ):  # type: ignore[return]
        """Context manager that times an operation and tracks statistics.

        Usage:
            monitor = PerformanceMonitor()
            with monitor.track("save_project"):
                save_project(...)

        Args:
            operation: Operation name (e.g., 'viewport_zoom', 'save_project').
            warn_threshold_ms: Override warning threshold. None = use default.
            **extra: Additional metadata for benchmark logging.
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.record(operation, duration_ms, warn_threshold_ms=warn_threshold_ms, **extra)

    def record(
        self,
        operation: str,
        duration_ms: float,
        *,
        warn_threshold_ms: float | None = None,
        **extra: Any,
    ) -> None:
        """Record an operation duration.

        Args:
            operation: Operation name.
            duration_ms: Duration in milliseconds.
            warn_threshold_ms: Override warning threshold. None = use default.
            **extra: Additional metadata for benchmark logging.
        """
        # Update rolling window
        if operation not in self._windows:
            self._windows[operation] = deque(maxlen=self._window_size)
        self._windows[operation].append(duration_ms)

        # Update totals
        self._total_counts[operation] = self._total_counts.get(operation, 0) + 1
        self._total_times[operation] = self._total_times.get(operation, 0.0) + duration_ms

        # Log to benchmark
        bench = self._get_benchmark()
        bench.record(operation, duration_ms, **extra)

        # Check warning threshold
        threshold = warn_threshold_ms if warn_threshold_ms is not None else self._warning_threshold_ms
        if duration_ms > threshold:
            logger.warning(
                "slow_operation",
                operation=operation,
                duration_ms=round(duration_ms, 2),
                threshold_ms=threshold,
            )

    def get_stats(self, operation: str) -> dict[str, Any]:
        """Get statistics for a specific operation.

        Args:
            operation: Operation name.

        Returns:
            Dict with count, mean_ms, min_ms, max_ms, p95_ms for recent window.
        """
        window = self._windows.get(operation, deque())
        if not window:
            return {
                "operation": operation,
                "count": 0,
                "mean_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p95_ms": 0.0,
                "total_count": self._total_counts.get(operation, 0),
                "total_ms": self._total_times.get(operation, 0.0),
            }

        from statistics import mean

        durations = list(window)
        sorted_d = sorted(durations)
        n = len(sorted_d)
        p95_idx = int(n * 0.95)

        return {
            "operation": operation,
            "count": n,
            "mean_ms": round(mean(durations), 3),
            "min_ms": round(sorted_d[0], 3),
            "max_ms": round(sorted_d[-1], 3),
            "p95_ms": round(sorted_d[min(p95_idx, n - 1)], 3),
            "total_count": self._total_counts.get(operation, 0),
            "total_ms": round(self._total_times.get(operation, 0.0), 3),
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all tracked operations.

        Returns:
            Dict mapping operation names to their stats.
        """
        return {op: self.get_stats(op) for op in self._windows}

    def clear(self) -> None:
        """Clear all rolling windows and totals."""
        self._windows.clear()
        self._total_counts.clear()
        self._total_times.clear()


# Convenience functions for common operations

def track_viewport_interaction(
    monitor: PerformanceMonitor,
    interaction_type: str,
) -> Any:
    """Create a tracked context manager for viewport interactions.

    Args:
        monitor: PerformanceMonitor instance.
        interaction_type: Type of interaction (zoom, pan, rotate).

    Returns:
        Context manager that records the interaction duration.
    """
    return monitor.track(f"viewport_{interaction_type}")


def track_save_operation(monitor: PerformanceMonitor, project_id: str = "") -> Any:
    """Create a tracked context manager for save operations.

    Args:
        monitor: PerformanceMonitor instance.
        project_id: Optional project identifier.

    Returns:
        Context manager that records the save duration.
    """
    extra = {"project_id": project_id} if project_id else {}
    return monitor.track("save_project", **extra)


def track_load_operation(monitor: PerformanceMonitor, project_id: str = "") -> Any:
    """Create a tracked context manager for load operations.

    Args:
        monitor: PerformanceMonitor instance.
        project_id: Optional project identifier.

    Returns:
        Context manager that records the load duration.
    """
    extra = {"project_id": project_id} if project_id else {}
    return monitor.track("load_project", **extra)


def track_thumbnail_generation(monitor: PerformanceMonitor, photo_count: int = 1) -> Any:
    """Create a tracked context manager for thumbnail generation.

    Args:
        monitor: PerformanceMonitor instance.
        photo_count: Number of thumbnails being generated.

    Returns:
        Context manager that records the generation duration.
    """
    return monitor.track("thumbnail_generate", photo_count=photo_count)
