"""Performance benchmark harness for timing key operations.

Provides decorators and context managers for measuring operation timing,
logging metrics to a structured file, and a CLI flag to enable benchmarking.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceBenchmark:
    """Collects and logs performance metrics for application operations.

    Metrics are written as JSON lines to a benchmark log file, enabling
    post-hoc analysis of timing data across sessions.

    Features:
    - Timing decorators for functions
    - Context managers for manual timing
    - JSON lines output for easy parsing
    - Configurable enable/disable via CLI flag or env var
    """

    def __init__(
        self,
        log_path: Path | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Initialize benchmark harness.

        Args:
            log_path: Path to benchmark log file. None = disabled.
            enabled: Override enable state. None = check env var.
        """
        if enabled is not None:
            self._enabled = enabled
        else:
            self._enabled = os.environ.get("HPM_BENCHMARK", "").lower() in ("1", "true", "yes")

        self._log_path = log_path
        self._metrics: list[dict[str, Any]] = []

        if self._enabled and self._log_path:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        """Whether benchmarking is active."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable benchmarking at runtime."""
        self._enabled = enabled

    def set_log_path(self, path: Path) -> None:
        """Set or change the log output path."""
        self._log_path = path
        if self._enabled and self._log_path:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        operation: str,
        duration_ms: float,
        **extra: Any,
    ) -> None:
        """Record a timing metric.

        Args:
            operation: Operation name (e.g., 'thumbnail_generate', 'save_project').
            duration_ms: Duration in milliseconds.
            **extra: Additional metadata to attach.
        """
        if not self._enabled:
            return

        metric = {
            "operation": operation,
            "duration_ms": round(duration_ms, 3),
            "timestamp": time.time(),
            **extra,
        }
        self._metrics.append(metric)
        logger.debug("benchmark_record operation=%s duration_ms=%.3f", operation, duration_ms)

        if self._log_path:
            self._flush(metric)

    def _flush(self, metric: dict[str, Any]) -> None:
        """Append a single metric to the log file."""
        if not self._log_path:
            return
        try:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(metric) + "\n")
        except OSError:
            logger.warning("benchmark_flush_failed path=%s", self._log_path)

    def get_metrics(self, operation: str | None = None) -> list[dict[str, Any]]:
        """Get recorded metrics, optionally filtered by operation.

        Args:
            operation: Filter to this operation name. None = all.

        Returns:
            List of metric dictionaries.
        """
        if operation:
            return [m for m in self._metrics if m["operation"] == operation]
        return list(self._metrics)

    def summary(self) -> dict[str, dict[str, float]]:
        """Generate summary statistics per operation.

        Returns:
            Dict mapping operation names to {count, mean_ms, min_ms, max_ms, p95_ms}.
        """
        from statistics import mean

        ops: dict[str, list[float]] = {}
        for m in self._metrics:
            ops.setdefault(m["operation"], []).append(m["duration_ms"])

        result: dict[str, dict[str, float]] = {}
        for op, durations in ops.items():
            sorted_d = sorted(durations)
            n = len(sorted_d)
            p95_idx = int(n * 0.95)
            result[op] = {
                "count": n,
                "mean_ms": round(mean(sorted_d), 3),
                "min_ms": round(sorted_d[0], 3),
                "max_ms": round(sorted_d[-1], 3),
                "p95_ms": round(sorted_d[min(p95_idx, n - 1)], 3),
            }
        return result

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


# Global benchmark instance
_benchmark: PerformanceBenchmark | None = None


def get_benchmark() -> PerformanceBenchmark:
    """Get or create the global benchmark instance."""
    global _benchmark
    if _benchmark is None:
        _benchmark = PerformanceBenchmark()
    return _benchmark


def init_benchmark(
    log_path: Path | None = None,
    enabled: bool | None = None,
) -> PerformanceBenchmark:
    """Initialize the global benchmark instance.

    Args:
        log_path: Path for benchmark log output.
        enabled: Override enable state.

    Returns:
        The global PerformanceBenchmark instance.
    """
    global _benchmark
    _benchmark = PerformanceBenchmark(log_path=log_path, enabled=enabled)
    return _benchmark


@contextmanager
def benchmark_timer(
    operation: str,
    *,
    benchmark: PerformanceBenchmark | None = None,
    **extra: Any,
):  # type: ignore[return]
    """Context manager that times a block and records the duration.

    Usage:
        with benchmark_timer("save_project", project_id="abc"):
            save_project(...)

    Args:
        operation: Operation name for the metric.
        benchmark: Benchmark instance to use. None = global instance.
        **extra: Additional metadata.
    """
    bench = benchmark or get_benchmark()
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        bench.record(operation, duration_ms, **extra)


def timed(
    operation: str | None = None,
    *,
    benchmark: PerformanceBenchmark | None = None,
) -> Callable[[F], F]:
    """Decorator that times a function call and records the duration.

    Usage:
        @timed("load_image")
        def load_image(path: str) -> QImage:
            ...

    Args:
        operation: Operation name. Defaults to the function's qualified name.
        benchmark: Benchmark instance to use. None = global instance.
    """

    def decorator(func: F) -> F:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bench = benchmark or get_benchmark()
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                bench.record(op_name, duration_ms)

        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__doc__ = func.__doc__
        return wrapper  # type: ignore[return-value]

    return decorator


def add_benchmark_args(parser: Any) -> None:
    """Add --benchmark flag to an argparse parser.

    Args:
        parser: argparse.ArgumentParser instance.
    """
    parser.add_argument(
        "--benchmark",
        action="store_true",
        default=False,
        help="Enable performance benchmarking (writes to .benchmark.jsonl)",
    )
    parser.add_argument(
        "--benchmark-log",
        type=str,
        default=".benchmark.jsonl",
        help="Path for benchmark log file (default: .benchmark.jsonl)",
    )


def setup_benchmark_from_args(args: Any) -> PerformanceBenchmark:
    """Initialize benchmark from parsed CLI arguments.

    Args:
        args: Parsed args with benchmark and benchmark_log attributes.

    Returns:
        Configured PerformanceBenchmark instance.
    """
    log_path = Path(args.benchmark_log) if args.benchmark else None
    return init_benchmark(log_path=log_path, enabled=args.benchmark)
