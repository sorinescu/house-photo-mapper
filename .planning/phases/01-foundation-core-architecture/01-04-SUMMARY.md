# Plan 01-04 Summary: Qt Memory-Safe Patterns

**Phase:** 01-foundation-core-architecture
**Plan:** 04
**Wave:** 3
**Status:** Complete
**Date:** 2025-07-13

## What Was Built

Established and enforced PySide6 memory-safe patterns across the codebase to prevent segfaults, memory leaks, and object lifetime bugs.

### Infrastructure

- **QtSafeViewModel** (`src/house_photo_mapper/infrastructure/qt_patterns.py`): Base class for all ViewModels
  - Enforces parent passing in `__init__` for Qt object tree management
  - Provides `safe_connect()` method that auto-wraps non-@Slot callables in `CallableSlotAdapter`
  - All ViewModels now inherit from this base

- **QtSafeRunnable** (`src/house_photo_mapper/infrastructure/qt_patterns.py`): Base class for background tasks
  - `setAutoDelete(False)` to prevent C++ side deleting while Python holds reference
  - Subclasses implement `run()` method

- **CallableSlotAdapter** (`src/house_photo_mapper/infrastructure/qt_patterns.py`): Wraps any callable as a proper @Slot
  - Solves lambda/closure memory leak problem (RESEARCH.md Pitfall #1)
  - Dynamically creates @Slot decorated method on adapter instance
  - Parented to owning ViewModel for automatic cleanup

- **safe_connect()** utility: Convenience function to connect signals safely

### ViewModel Updates

- **ProjectViewModel** (`src/house_photo_mapper/presentation/viewmodels/project_vm.py`): Now inherits `QtSafeViewModel`
- **MainWindowViewModel** (`src/house_photo_mapper/presentation/viewmodels/main_window_vm.py`): Now inherits `QtSafeViewModel`

### Linting Rules

Added to `pyproject.toml`:
- Ruff rule `PYI024` (pyqt-slot) to catch missing @Slot decorators
- MyPy strict mode already catches type issues

## Tests Passing

All 15 new tests pass:
- `QtSafeViewModel`: parent handling, safe_connect with lambdas and @Slot methods
- `CallableSlotAdapter`: wraps lambdas, methods, parent management, slot decoration
- `safe_connect`: direct @Slot connection, lambda wrapping, sender-as-parent fallback
- `QtSafeRunnable`: autoDelete=False, NotImplementedError on base run()

Plus all existing 25 tests still pass (38 total, 2 skipped)

## Requirements Satisfied

- CP-01: Memory safety foundation established

## Files Created/Modified

### New Files
- `src/house_photo_mapper/infrastructure/qt_patterns.py`
- `tests/unit/test_qt_patterns.py`

### Modified Files
- `src/house_photo_mapper/infrastructure/__init__.py` (exports new patterns)
- `src/house_photo_mapper/presentation/viewmodels/project_vm.py` (inherits QtSafeViewModel)
- `src/house_photo_mapper/presentation/viewmodels/main_window_vm.py` (inherits QtSafeViewModel)
- `pyproject.toml` (added PYI024 to Ruff rules)

## Verification Commands

```bash
uv run pytest tests/unit/test_qt_patterns.py -v
uv run pytest tests/ -v
uv run ruff check src/house_photo_mapper/presentation/viewmodels/
uv run mypy src/house_photo_mapper/presentation/viewmodels/
```