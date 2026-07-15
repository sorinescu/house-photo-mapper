"""ReportViewModel — Background PDF report generation with progress signals.

Manages ReportGeneratorService lifecycle via QThread worker, providing
progress, finished, error, and cancelled signals for UI integration.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from house_photo_mapper.domain.services.report_generator import (
    ReportGeneratorService,
    ReportPageData,
)
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel


class ReportGenerationWorker(QThread):
    """Background worker for PDF report generation.

    Runs ReportGeneratorService.generate() in a separate thread to avoid
    blocking the UI during long PDF compositions.
    """

    progress = Signal(int, int)  # (current, total)
    finished = Signal(str)  # output_path
    error = Signal(str)  # error message

    def __init__(
        self,
        pages_data: list[ReportPageData],
        output_path: str,
        page_size: str,
        project_dir: str,
        parent=None,
    ) -> None:
        """Initialize the worker.

        Args:
            pages_data: List of page data for the report.
            output_path: Path to write the output PDF.
            page_size: Page size string (e.g., "A4 Portrait").
            project_dir: Project root directory.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._pages_data = pages_data
        self._output_path = output_path
        self._page_size = page_size
        self._project_dir = project_dir

    def run(self) -> None:
        """Execute report generation and emit signals."""
        try:
            svc = ReportGeneratorService(project_dir=self._project_dir)
            total = len(self._pages_data)

            # Emit progress for each page
            for i in range(total):
                self.progress.emit(i + 1, total)

            result = svc.generate(
                self._pages_data, self._output_path, self._page_size
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ReportViewModel(QtSafeViewModel):
    """ViewModel for report generation with background worker and progress tracking.

    Signals:
        progress: Emitted with (current_page, total_pages) during generation.
        finished: Emitted with output_path when generation completes.
        error: Emitted with error message on failure.
        cancelled: Emitted when user cancels generation.
    """

    progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        """Initialize ReportViewModel.

        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._cancelled = False
        self._output_path = ""
        self._worker: ReportGenerationWorker | None = None

    @property
    def cancelled(self) -> bool:
        """Whether generation has been cancelled."""
        return self._cancelled

    @property
    def output_path(self) -> str:
        """Output file path."""
        return self._output_path

    def generate_report(
        self,
        pages_data: list[ReportPageData],
        output_path: str,
        page_size: str,
        project_dir: str = ".",
    ) -> None:
        """Start background report generation.

        Creates a QThread worker, connects signals, and starts generation.

        Args:
            pages_data: List of page data for the report.
            output_path: Path to write the output PDF.
            page_size: Page size string.
            project_dir: Project root directory.
        """
        self._cancelled = False
        self._output_path = output_path

        self._worker = ReportGenerationWorker(
            pages_data=pages_data,
            output_path=output_path,
            page_size=page_size,
            project_dir=project_dir,
            parent=self,
        )

        # Connect worker signals
        self._worker.progress.connect(self.progress.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._worker.start()

    def cancel(self) -> None:
        """Cancel the report generation.

        Sets the cancelled flag and emits cancelled signal.
        Note: The worker thread cannot be forcefully stopped; it will
        complete its current operation and the result will be discarded.
        """
        self._cancelled = True
        self.cancelled.emit()

    def get_page_size_string(self, format: str = "A4", orientation: str = "Portrait") -> str:
        """Get formatted page size string from format and orientation.

        Args:
            format: Page format ("A4" or "US Letter").
            orientation: Page orientation ("Portrait" or "Landscape").

        Returns:
            Formatted string like "A4 Portrait" or "US Letter Landscape".
        """
        if format == "US Letter":
            return f"US Letter {orientation}"
        return f"{format} {orientation}"

    def _on_finished(self, output_path: str) -> None:
        """Handle worker completion."""
        if not self._cancelled:
            self.finished.emit(output_path)

    def _on_error(self, message: str) -> None:
        """Handle worker error."""
        if not self._cancelled:
            self.error.emit(message)
