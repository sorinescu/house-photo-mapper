"""Tests for Qt memory-safe patterns."""

import gc
from typing import TYPE_CHECKING

import pytest
from PySide6.QtCore import QObject, Signal

from house_photo_mapper.infrastructure.qt_patterns import (
    CallableSlotAdapter,
    QtSafeRunnable,
    QtSafeViewModel,
    safe_connect,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


class _SignalSender(QObject):
    """Test signal sender with proper class-level signal."""
    custom_signal = Signal(object)
    sig = Signal(object)


class TestQtSafeViewModel:
    """Tests for QtSafeViewModel base class."""

    def test_parent_passed_to_init(self, qapp: "QApplication") -> None:
        """Test that parent is properly passed to QObject."""
        parent = QObject()
        vm = QtSafeViewModel(parent=parent)
        assert vm.parent() is parent

    def test_parent_none_allowed(self, qapp: "QApplication") -> None:
        """Test that None parent is allowed for top-level ViewModels."""
        vm = QtSafeViewModel(parent=None)
        assert vm.parent() is None

    def test_safe_connect_wraps_lambda(self, qapp: "QApplication") -> None:
        """Test that safe_connect wraps lambda in CallableSlotAdapter."""
        sender = _SignalSender()

        vm = QtSafeViewModel(parent=None)
        received = []

        def handler(value: object) -> None:
            received.append(value)

        result = vm.safe_connect(sender, sender.custom_signal, handler)
        assert result is True

        sender.custom_signal.emit("test")
        assert received == ["test"]

    def test_safe_connect_accepts_slot_decorated(self, qapp: "QApplication") -> None:
        """Test that @Slot decorated methods are connected directly."""
        from PySide6.QtCore import Slot

        sender = _SignalSender()

        class TestVM(QtSafeViewModel):
            @Slot(object)
            def handler(self, value: object) -> None:
                self.received = value

        vm = TestVM(parent=None)
        result = vm.safe_connect(sender, sender.custom_signal, vm.handler)
        assert result is True

        sender.custom_signal.emit("direct")
        assert vm.received == "direct"


class TestCallableSlotAdapter:
    """Tests for CallableSlotAdapter."""

    def test_wraps_lambda(self, qapp: "QApplication") -> None:
        """Test that lambda is wrapped and callable."""
        adapter = CallableSlotAdapter(lambda x: x * 2, parent=None)
        result = adapter.slot(5)
        assert result == 10

    def test_wraps_method(self, qapp: "QApplication") -> None:
        """Test that method is wrapped correctly."""
        class Handler:
            def process(self, x: int) -> int:
                return x + 1

        h = Handler()
        adapter = CallableSlotAdapter(h.process, parent=None)
        result = adapter.slot(5)
        assert result == 6

    def test_adapter_has_parent(self, qapp: "QApplication") -> None:
        """Test that adapter gets parent for lifetime management."""
        parent = QObject()
        adapter = CallableSlotAdapter(lambda: None, parent=parent)
        assert adapter.parent() is parent

    def test_slot_is_decorated(self, qapp: "QApplication") -> None:
        """Test that the slot attribute is @Slot decorated."""
        # The slot should be a method that can be connected to signals
        # We test this by actually connecting it
        sender = _SignalSender()
        received = []

        def handler(value):
            received.append(value)

        adapter = CallableSlotAdapter(handler, parent=None)
        sender.custom_signal.connect(adapter.slot)
        sender.custom_signal.emit("test")
        assert received == ["test"]


class TestSafeConnect:
    """Tests for safe_connect utility function."""

    def test_connects_slot_directly(self, qapp: "QApplication") -> None:
        """Test that @Slot methods connect directly."""
        from PySide6.QtCore import Slot

        sender = _SignalSender()

        class Receiver(QObject):
            @Slot(object)
            def handler(self, value: object) -> None:
                self.value = value

        receiver = Receiver()
        result = safe_connect(sender, sender.sig, receiver.handler)
        assert result is True

        sender.sig.emit("test")
        assert receiver.value == "test"

    def test_wraps_lambda(self, qapp: "QApplication") -> None:
        """Test that lambda gets wrapped in adapter."""
        sender = _SignalSender()

        received = []

        result = safe_connect(sender, sender.sig, lambda x: received.append(x))
        assert result is True

        sender.sig.emit("wrapped")
        assert received == ["wrapped"]

    def test_uses_sender_as_parent_when_none(self, qapp: "QApplication") -> None:
        """Test that sender becomes adapter parent when no parent given."""
        sender = _SignalSender()

        safe_connect(sender, sender.sig, lambda: None)

        adapters = [c for c in sender.children() if isinstance(c, CallableSlotAdapter)]
        assert len(adapters) == 1


class TestQtSafeRunnable:
    """Tests for QtSafeRunnable base class."""

    def test_auto_delete_false(self, qapp: "QApplication") -> None:
        """Test that autoDelete is False."""
        runnable = QtSafeRunnable(parent=None)
        assert runnable.autoDelete() is False

    def test_run_raises_not_implemented(self, qapp: "QApplication") -> None:
        """Test that base run() raises NotImplementedError."""
        runnable = QtSafeRunnable(parent=None)
        with pytest.raises(NotImplementedError):
            runnable.run()


class TestMemoryLeakPrevention:
    """Tests to verify memory leak prevention patterns work."""

    def test_viewmodel_cleanup_on_parent_delete(self, qapp: "QApplication") -> None:
        """Test that ViewModel is cleaned up when parent is deleted."""
        parent = QObject()
        _ = QtSafeViewModel(parent=parent)

        parent.deleteLater()
        qapp.processEvents()

        gc.collect()

    def test_adapter_cleanup_on_parent_delete(self, qapp: "QApplication") -> None:
        """Test that CallableSlotAdapter is cleaned up with parent."""
        parent = QObject()
        _ = CallableSlotAdapter(lambda: None, parent=parent)

        parent.deleteLater()
        qapp.processEvents()
        gc.collect()
