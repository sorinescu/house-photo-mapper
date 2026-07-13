"""Qt Memory-Safe Patterns for PySide6.

Provides base classes and utilities to prevent common PySide6 memory management issues:
- QtSafeViewModel: QObject base with enforced parent, safe signal connection
- QtSafeRunnable: QRunnable base with auto-delete disabled, explicit cleanup
- CallableSlotAdapter: Wraps any callable as a @Slot for safe signal connections
- safe_connect: Utility to connect signals safely (auto-wraps non-@Slot callables)

Reference: RESEARCH.md Pitfalls #1 (lambda memory leaks) and #5 (QRunnable auto-delete race).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QRunnable, Slot

if TYPE_CHECKING:
    from PySide6.QtCore import QObject as QObjectType

SignalInstance = Any


class QtSafeViewModel(QObject):
    """Base class for all ViewModels enforcing memory-safe Qt patterns.

    Rules enforced:
    - Parent must be passed to __init__ (or explicitly set to None for top-level)
    - All signal handlers must use @Slot() decorator
    - Use safe_connect() for connecting signals to avoid lambda leaks
    """

    def __init__(self, parent: QObjectType | None = None) -> None:
        """Initialize with required parent for Qt object tree management.

        Args:
            parent: Parent QObject for automatic cleanup. Top-level ViewModels
                may pass None but should be owned by the main window.
        """
        super().__init__(parent)

    def safe_connect(
        self,
        sender: QObjectType,
        signal: SignalInstance,
        slot: Callable[..., Any],
        *,
        connection_type: int = 0,  # Qt.ConnectionType.AutoConnection
    ) -> bool:
        """Safely connect a signal to a slot, wrapping non-@Slot callables.

        If slot is not decorated with @Slot(), wraps it in a CallableSlotAdapter
        with this ViewModel as parent, ensuring proper lifetime management.

        Args:
            sender: Object emitting the signal.
            signal: Signal to connect.
            slot: Callable to connect (will be wrapped if not @Slot decorated).
            connection_type: Qt connection type.

        Returns:
            True if connection succeeded.
        """
        if not self._is_slot_decorated(slot):
            adapter = CallableSlotAdapter(slot, parent=self)
            slot = adapter.slot

        try:
            signal.connect(slot, connection_type)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_slot_decorated(func: Callable[..., Any]) -> bool:
        """Check if a function has @Slot() decorator."""
        return hasattr(func, "__pyqt_slot__") or hasattr(func, "__slot__")


class QtSafeRunnable(QRunnable):
    """Base class for QRunnable tasks with explicit lifetime management.

    Rules enforced:
    - setAutoDelete(False) to prevent C++ side deleting while Python holds ref
    - Store reference in parent ViewModel to prevent premature GC
    """

    def __init__(self, parent: QObjectType | None = None) -> None:
        """Initialize with parent for lifetime tracking.

        Args:
            parent: Parent QObject (typically the ViewModel that owns this task).
        """
        super().__init__()
        self.setAutoDelete(False)
        self._parent = parent

    def run(self) -> None:
        """Override in subclass to implement task logic."""
        raise NotImplementedError("Subclasses must implement run()")


class CallableSlotAdapter(QObject):
    """Adapter that wraps any callable as a @Slot for safe signal connections.

    Solves the lambda/closure memory leak problem (RESEARCH.md Pitfall #1):
    Connecting `button.clicked.connect(lambda: self.do_something())` creates
    a closure that holds `self`, preventing garbage collection and causing
    segfaults when the C++ object is deleted.

    Usage:
        adapter = CallableSlotAdapter(lambda x: self.handle(x), parent=self)
        sender.signal.connect(adapter.slot)
    """

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        parent: QObjectType | None = None,
    ) -> None:
        """Create adapter for a callable.

        Args:
            func: The callable to wrap. Can be lambda, partial, or any callable.
            parent: Parent QObject for automatic cleanup when parent is deleted.
        """
        super().__init__(parent)
        self._func = func

        # Create the slot method directly on this instance
        self._create_slot()

    def _create_slot(self) -> None:
        """Create a proper @Slot method that calls the wrapped function."""

        @Slot(object)
        def _slot(*args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

        self.slot = _slot


def safe_connect(
    sender: QObjectType,
    signal: SignalInstance,
    slot: Callable[..., Any],
    *,
    parent: QObjectType | None = None,
    connection_type: int = 0,
) -> bool:
    """Connect signal to slot, auto-wrapping non-@Slot callables.

    If slot is not @Slot decorated, wraps it in a CallableSlotAdapter with
    the given parent (or sender if no parent provided).

    Args:
        sender: Object emitting the signal.
        signal: Signal to connect.
        slot: Callable to connect (will be wrapped if needed).
        parent: Parent for adapter if slot needs wrapping. Defaults to sender.
        connection_type: Qt connection type.

    Returns:
        True if connection succeeded.
    """
    if hasattr(slot, "__pyqt_slot__") or hasattr(slot, "__slot__"):
        try:
            signal.connect(slot, connection_type)
            return True
        except Exception:
            return False

    adapter_parent = parent or sender
    adapter = CallableSlotAdapter(slot, parent=adapter_parent)
    try:
        signal.connect(adapter.slot, connection_type)
        return True
    except Exception:
        return False
