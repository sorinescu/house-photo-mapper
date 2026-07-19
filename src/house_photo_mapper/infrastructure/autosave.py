"""AutoSaveManager - Automatic project saving with background serialization.

Provides periodic auto-save functionality using QTimer for scheduling and
QThreadPool for background serialization to avoid UI freezes.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QMutex, QMutexLocker, QTimer, Signal, Slot
from PySide6.QtCore import QThreadPool, QRunnable

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_MS = 120_000  # 2 minutes in milliseconds


class SaveWorker(QRunnable):
    """Background worker for thread-safe project serialization.

    Encapsulates the save operation to run on a QThreadPool, preventing
    UI freezes during file I/O. Uses a mutex to safely access project data.
    """

    class _Signals(QObject):
        """Internal signal carrier for cross-thread communication."""

        completed = Signal(bool, str)  # (success, error_message)

    def __init__(
        self,
        project_vm: "ProjectViewModel",
        mutex: QMutex,
    ) -> None:
        """Initialize SaveWorker.

        Args:
            project_vm: ProjectViewModel to save.
            mutex: Mutex for thread-safe access to project data.
        """
        super().__init__()
        self.setAutoDelete(False)
        self._project_vm = project_vm
        self._mutex = mutex
        self._signals = self._Signals()

    @property
    def completed(self) -> Signal:
        """Signal emitted when save completes."""
        return self._signals.completed

    def run(self) -> None:
        """Execute the save operation in background thread."""
        locker = QMutexLocker(self._mutex)
        try:
            self._project_vm.save_project()
            self._signals.completed.emit(True, "")
        except Exception as e:
            logger.error("Auto-save failed: %s", e)
            self._signals.completed.emit(False, str(e))


class AutoSaveManager(QObject):
    """Manages automatic project saving on a configurable interval.

    Features:
    - QTimer-based periodic save triggers
    - Dirty flag checking before save (skips if clean)
    - Background serialization via QThreadPool to prevent UI freezes
    - Mutex protection for concurrent access to project data
    - Signals for save status updates (status bar integration)
    - Prevents concurrent saves via is_saving guard
    """

    save_started = Signal()
    save_completed = Signal(bool, str)  # (success, error_message)

    def __init__(
        self,
        project_vm: "ProjectViewModel",
        interval_ms: int = DEFAULT_INTERVAL_MS,
        parent: QObject | None = None,
    ) -> None:
        """Initialize AutoSaveManager.

        Args:
            project_vm: ProjectViewModel to auto-save.
            interval_ms: Save interval in milliseconds (default: 120000 = 2 min).
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._project_vm = project_vm
        self._interval_ms = interval_ms
        self._mutex = QMutex()
        self._is_saving = False
        self._enabled = True

        # Timer for periodic save triggers
        self._timer = QTimer(self)
        self._timer.setInterval(self._interval_ms)
        self._timer.timeout.connect(self._on_timer_tick)

        # Thread pool for background saves (max 1 concurrent worker)
        self._pool = QThreadPool.globalInstance()

    @property
    def is_saving(self) -> bool:
        """Return True if a save operation is currently in progress."""
        return self._is_saving

    @property
    def enabled(self) -> bool:
        """Return True if auto-save is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable auto-save.

        Args:
            value: True to enable, False to disable.
        """
        self._enabled = value
        if not value:
            self._timer.stop()

    @property
    def interval_ms(self) -> int:
        """Return current interval in milliseconds."""
        return self._interval_ms

    @interval_ms.setter
    def interval_ms(self, value: int) -> None:
        """Set the save interval.

        Args:
            value: Interval in milliseconds.
        """
        self._interval_ms = max(1000, value)  # minimum 1 second
        self._timer.setInterval(self._interval_ms)

    def start(self) -> None:
        """Start the auto-save timer."""
        if self._enabled and not self._timer.isActive():
            self._timer.start()
            logger.debug("Auto-save timer started (interval=%dms)", self._interval_ms)

    def stop(self) -> None:
        """Stop the auto-save timer."""
        self._timer.stop()
        logger.debug("Auto-save timer stopped")

    def save_now(self) -> None:
        """Trigger an immediate save if project is dirty and not already saving."""
        self._perform_save()

    def save_now(self) -> None:
        """Trigger an immediate save if project has a path and not already saving."""
        if self._is_saving:
            logger.debug("save_now: skipped, already saving")
            return
        if self._project_vm.project is None or not self._project_vm.project.path:
            logger.debug("save_now: skipped, no project or no path (project=%s, path=%r)",
                         self._project_vm.project, 
                         self._project_vm.project.path if self._project_vm.project else None)
            return
        logger.debug("save_now: triggering save for %s", self._project_vm.project.path)
        self._perform_save()

    def cancel_pending(self) -> None:
        """Cancel any pending save and stop the timer."""
        self._timer.stop()

    def _on_timer_tick(self) -> None:
        """Handle timer tick - check dirty flag and trigger save."""
        if not self._enabled:
            return
        self._perform_save()

    def _perform_save(self) -> None:
        """Perform the save if conditions are met."""
        if self._is_saving:
            logger.debug("Auto-save skipped: save already in progress")
            return

        if not self._project_vm.dirty:
            logger.debug("Auto-save skipped: project is clean")
            return

        if self._project_vm.project is None:
            logger.debug("Auto-save skipped: no project loaded")
            return

        self._is_saving = True
        self.save_started.emit()

        worker = SaveWorker(self._project_vm, self._mutex)
        worker.completed.connect(self._on_save_completed)
        self._pool.start(worker)

    @Slot(bool, str)
    def _on_save_completed(self, success: bool, error_message: str) -> None:
        """Handle save completion.

        Args:
            success: True if save succeeded.
            error_message: Error message if save failed.
        """
        self._is_saving = False
        if success:
            logger.debug("Auto-save completed successfully")
        else:
            logger.warning("Auto-save failed: %s", error_message)
        self.save_completed.emit(success, error_message)
