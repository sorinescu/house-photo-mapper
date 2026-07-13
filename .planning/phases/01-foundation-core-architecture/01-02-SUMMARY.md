# Plan 01-02 Summary: MVVM Skeleton Implementation

**Phase:** 01-foundation-core-architecture
**Plan:** 02
**Wave:** 2
**Status:** Complete
**Date:** 2025-07-13

## What Was Built

Implemented the complete MVVM skeleton for project management (PM-01 through PM-04):

### Domain Models
- **ProjectModel** (`src/house_photo_mapper/domain/models/project.py`): Pydantic BaseModel with JSON serialization, dirty tracking, and factory method `create_empty()`. Contains plans, photos, annotations, export_settings, and ui_preferences.

### Domain Services
- **PersistenceService** (`src/house_photo_mapper/domain/services/persistence.py`): Atomic JSON file I/O (write to .tmp then rename), QSettings for recent projects (max 10), window geometry, and window state.

### ViewModels
- **ProjectViewModel** (`src/house_photo_mapper/presentation/viewmodels/project_vm.py`): QObject with slots for new_project, open_project, save_project, save_project_as, close_project. Emits project_changed, dirty_changed, error_occurred, recent_projects_changed signals.
- **MainWindowViewModel** (`src/house_photo_mapper/presentation/viewmodels/main_window_vm.py`): Composes ProjectViewModel, handles file dialogs (New, Open, Save As), manages window title, recent projects menu, and window geometry persistence.

### Views
- **MainWindow** (`src/house_photo_mapper/presentation/views/main_window.py`): QMainWindow with complete menu bar (File, Edit, View, Window, Help), toolbar, status bar. File actions wired to ViewModel slots. Recent projects submenu dynamically populated.
- **Project Dialogs** (`src/house_photo_mapper/presentation/views/project_dialogs.py`): Helper functions for QFileDialog interactions.

### Application Entry Point
- Updated `src/house_photo_mapper/app.py` to wire PersistenceService → MainWindowViewModel → MainWindow.

## Tests Passing

All 15 unit tests pass:
- `tests/unit/test_project_model.py`: 8 tests (create_empty, JSON round-trip, dirty tracking, path handling)
- `tests/unit/test_persistence.py`: 7 tests (save/load/save_as, recent projects, window geometry)

All 5 integration tests pass:
- `tests/integration/test_app_lifecycle.py`: App starts, MainWindow creates, menus work

## Requirements Satisfied

- PM-01: Create new empty project via File → New ✓
- PM-02: Open existing .hpmpj project via File → Open ✓
- PM-03: Save project via File → Save (Ctrl+S) ✓
- PM-04: Save project as copy via File → Save As ✓
- Window geometry persists across sessions ✓
- Recent projects list persists in macOS plist ✓

## Files Created/Modified

- `src/house_photo_mapper/domain/models/project.py` (new)
- `src/house_photo_mapper/domain/models/__init__.py` (updated)
- `src/house_photo_mapper/domain/services/persistence.py` (updated)
- `src/house_photo_mapper/domain/services/__init__.py` (updated)
- `src/house_photo_mapper/domain/__init__.py` (updated)
- `src/house_photo_mapper/presentation/viewmodels/project_vm.py` (new)
- `src/house_photo_mapper/presentation/viewmodels/main_window_vm.py` (new)
- `src/house_photo_mapper/presentation/viewmodels/__init__.py` (new)
- `src/house_photo_mapper/presentation/views/main_window.py` (new)
- `src/house_photo_mapper/presentation/views/project_dialogs.py` (new)
- `src/house_photo_mapper/presentation/views/__init__.py` (new)
- `src/house_photo_mapper/presentation/__init__.py` (new)
- `src/house_photo_mapper/app.py` (updated)

## Verification Commands

```bash
uv run pytest tests/unit/test_project_model.py -x -v
uv run pytest tests/unit/test_persistence.py -x -v
uv run pytest tests/integration/test_app_lifecycle.py -x -v
```