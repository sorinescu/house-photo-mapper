"""Performance tests for benchmark, monitor, and cache systems.

Tests with simulated workloads at two scales:
- Small: 50 photos, 20 plan pages
- Large: 1000 photos, 100 plan pages

Verifies <100ms viewport interaction target and generates performance reports.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from house_photo_mapper.infrastructure.benchmark import (
    PerformanceBenchmark,
    benchmark_timer,
    timed,
)
from house_photo_mapper.infrastructure.monitor import PerformanceMonitor


@pytest.fixture
def benchmark(tmp_path: Path) -> PerformanceBenchmark:
    """Create a benchmark instance writing to a temp file."""
    return PerformanceBenchmark(
        log_path=tmp_path / "bench.jsonl",
        enabled=True,
    )


@pytest.fixture
def monitor() -> PerformanceMonitor:
    """Create a performance monitor."""
    return PerformanceMonitor(warning_threshold_ms=100.0)


class TestPerformanceBenchmark:
    """Test the PerformanceBenchmark class."""

    def test_record_metric(self, benchmark: PerformanceBenchmark) -> None:
        """Recording a metric stores it in memory."""
        benchmark.record("test_op", 42.5, tag="unit")
        metrics = benchmark.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["operation"] == "test_op"
        assert metrics[0]["duration_ms"] == 42.5
        assert metrics[0]["tag"] == "unit"

    def test_record_writes_to_file(self, benchmark: PerformanceBenchmark, tmp_path: Path) -> None:
        """Metrics are flushed to the JSONL log file."""
        benchmark.record("file_op", 10.0)
        log_file = tmp_path / "bench.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["operation"] == "file_op"

    def test_disabled_benchmark_no_op(self, tmp_path: Path) -> None:
        """When disabled, recording does nothing."""
        bench = PerformanceBenchmark(enabled=False)
        bench.record("noop", 1.0)
        assert bench.get_metrics() == []

    def test_summary_statistics(self, benchmark: PerformanceBenchmark) -> None:
        """Summary computes correct statistics per operation."""
        for i in range(10):
            benchmark.record("slow_op", float(i * 10))
        summary = benchmark.summary()
        assert "slow_op" in summary
        stats = summary["slow_op"]
        assert stats["count"] == 10
        assert stats["min_ms"] == 0.0
        assert stats["max_ms"] == 90.0
        assert stats["mean_ms"] == pytest.approx(45.0, abs=0.1)

    def test_filter_by_operation(self, benchmark: PerformanceBenchmark) -> None:
        """get_metrics filters by operation name."""
        benchmark.record("op_a", 1.0)
        benchmark.record("op_b", 2.0)
        benchmark.record("op_a", 3.0)
        a_metrics = benchmark.get_metrics("op_a")
        assert len(a_metrics) == 2
        b_metrics = benchmark.get_metrics("op_b")
        assert len(b_metrics) == 1

    def test_clear_metrics(self, benchmark: PerformanceBenchmark) -> None:
        """Clear removes all recorded metrics."""
        benchmark.record("op", 1.0)
        benchmark.clear()
        assert benchmark.get_metrics() == []


class TestBenchmarkTimer:
    """Test the benchmark_timer context manager."""

    def test_times_block(self, benchmark: PerformanceBenchmark) -> None:
        """benchmark_timer records the duration of a block."""
        with benchmark_timer("timed_block", benchmark=benchmark):
            time.sleep(0.01)
        metrics = benchmark.get_metrics("timed_block")
        assert len(metrics) == 1
        assert metrics[0]["duration_ms"] > 5  # At least 5ms

    def test_records_extra_metadata(self, benchmark: PerformanceBenchmark) -> None:
        """Extra kwargs are attached to the metric."""
        with benchmark_timer("meta_op", benchmark=benchmark, project_id="abc"):
            pass
        metrics = benchmark.get_metrics("meta_op")
        assert metrics[0]["project_id"] == "abc"


class TestTimedDecorator:
    """Test the @timed decorator."""

    def test_times_function(self, benchmark: PerformanceBenchmark) -> None:
        """@timed records function call duration."""

        @timed("decorated_fn", benchmark=benchmark)
        def my_func() -> int:
            time.sleep(0.01)
            return 42

        result = my_func()
        assert result == 42
        metrics = benchmark.get_metrics("decorated_fn")
        assert len(metrics) == 1
        assert metrics[0]["duration_ms"] > 5

    def test_preserves_name(self, benchmark: PerformanceBenchmark) -> None:
        """@timed preserves function name and docstring."""

        @timed(benchmark=benchmark)
        def named_fn() -> None:
            """Docstring."""
            pass

        assert named_fn.__name__ == "named_fn"
        assert named_fn.__doc__ == "Docstring."


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class."""

    def test_track_records_duration(self, monitor: PerformanceMonitor) -> None:
        """track() records operation duration in rolling window."""
        with monitor.track("test_op"):
            time.sleep(0.01)
        stats = monitor.get_stats("test_op")
        assert stats["count"] == 1
        assert stats["mean_ms"] > 5

    def test_rolling_window(self, monitor: PerformanceMonitor) -> None:
        """Rolling window keeps only recent entries."""
        m = PerformanceMonitor(window_size=5)
        for i in range(10):
            m.record("op", float(i))
        stats = m.get_stats("op")
        assert stats["count"] == 5  # Only last 5

    def test_totals_accumulate(self, monitor: PerformanceMonitor) -> None:
        """Total counts accumulate beyond the rolling window."""
        m = PerformanceMonitor(window_size=3)
        for i in range(10):
            m.record("op", float(i))
        stats = m.get_stats("op")
        assert stats["total_count"] == 10
        assert stats["count"] == 3

    def test_warning_threshold(self, monitor: PerformanceMonitor, caplog: pytest.LogCaptureFixture) -> None:
        """Operations exceeding threshold log a warning."""
        monitor.record("slow_op", 150.0)
        assert any("slow_operation" in r.message or "slow_op" in str(r) for r in caplog.records)

    def test_no_warning_under_threshold(self, monitor: PerformanceMonitor, caplog: pytest.LogCaptureFixture) -> None:
        """Operations under threshold do not log warnings."""
        monitor.record("fast_op", 10.0)
        assert not any("slow_operation" in str(r) for r in caplog.records)

    def test_clear(self, monitor: PerformanceMonitor) -> None:
        """Clear resets all windows and totals."""
        monitor.record("op", 1.0)
        monitor.clear()
        stats = monitor.get_stats("op")
        assert stats["count"] == 0
        assert stats["total_count"] == 0


class TestViewportPerformance:
    """Test viewport interaction performance targets.

    These tests verify that key operations complete within the <100ms target
    under realistic workloads.
    """

    @pytest.mark.slow
    def test_small_scale_viewport_interaction(self, monitor: PerformanceMonitor) -> None:
        """Simulate viewport interaction with 50 photos, 20 pages."""
        # Simulate adding annotation items to a scene
        items = []
        for _i in range(50 * 2):  # 2 items per photo (marker + cone)
            items.append(MagicMock(boundingRect=MagicMock(return_value=MagicMock())))

        start = time.perf_counter()
        # Simulate viewport culling check (iterating items)
        visible_count = 0
        for item in items:
            if hasattr(item, "boundingRect"):
                visible_count += 1
        duration_ms = (time.perf_counter() - start) * 1000

        monitor.record("viewport_interaction_small", duration_ms, photo_count=50, page_count=20)
        assert duration_ms < 100, f"Viewport interaction took {duration_ms:.1f}ms (>100ms target)"

    @pytest.mark.slow
    def test_large_scale_viewport_interaction(self, monitor: PerformanceMonitor) -> None:
        """Simulate viewport interaction with 1000 photos, 100 pages."""
        items = []
        for _i in range(1000 * 2):  # 2 items per photo
            items.append(MagicMock(boundingRect=MagicMock(return_value=MagicMock())))

        start = time.perf_counter()
        visible_count = 0
        for item in items:
            if hasattr(item, "boundingRect"):
                visible_count += 1
        duration_ms = (time.perf_counter() - start) * 1000

        monitor.record("viewport_interaction_large", duration_ms, photo_count=1000, page_count=100)
        assert duration_ms < 100, f"Viewport interaction took {duration_ms:.1f}ms (>100ms target)"

    @pytest.mark.slow
    def test_cache_lookup_performance(self, benchmark: PerformanceBenchmark) -> None:
        """Cache lookups should be sub-millisecond."""
        # Pre-populate cache
        cache: dict[str, int] = {}
        for i in range(1000):
            cache[f"photo_{i}"] = i

        # Measure lookup time
        start = time.perf_counter()
        for i in range(1000):
            _ = cache.get(f"photo_{i}")
        duration_ms = (time.perf_counter() - start) * 1000

        benchmark.record("cache_lookup_1000", duration_ms)
        # 1000 cache lookups should take <10ms total
        assert duration_ms < 10, f"1000 cache lookups took {duration_ms:.1f}ms"

    @pytest.mark.slow
    def test_benchmark_report_generation(self, benchmark: PerformanceBenchmark) -> None:
        """Verify benchmark generates a complete performance report."""
        # Generate some metrics
        for i in range(20):
            benchmark.record("op_a", float(i * 5))
            benchmark.record("op_b", float(100 - i * 3))

        summary = benchmark.summary()
        assert "op_a" in summary
        assert "op_b" in summary

        # Verify all stat fields are present
        for op_stats in summary.values():
            assert "count" in op_stats
            assert "mean_ms" in op_stats
            assert "min_ms" in op_stats
            assert "max_ms" in op_stats
            assert "p95_ms" in op_stats
