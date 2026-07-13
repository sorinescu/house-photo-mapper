---
phase: 02-plan-system
plan: 06
subsystem: ui
tags: [pyside6, qt, file-dialog, plan-import, mvvm]

requires:
  - phase: 02-plan-system
    provides: PlanViewModel with load_plan_from_pdf/load_plan_from_image methods
provides:
  - "Import Plan... menu action with file dialog and extension-based routing"
  - "MainWindowViewModel.import_plan slot wiring File dialog to PlanViewModel"
affects: [02-plan-system]

tech-stack:
  added: []
  patterns: [file-dialog-routing, standalone-import]

key-files:
  created:
    - tests/test_plan_import_ui.py
  modified:
    - src/house_photo_mapper/presentation/viewmodels/main_window_vm.py
    - src/house_photo_mapper/presentation/viewmodels/project_vm.py
    - src/house_photo_mapper/presentation/views/main_window.py

key-decisions:
  - "Standalone import: no project required to import a plan"
  - "ProjectViewModel.plan_vm property exposes PlanViewModel for MainWindowViewModel access"

patterns-established:
  - "File dialog routing: QFileDialog → extension check → delegate to appropriate ViewModel method"

requirements-completed: [PI-01, PI-02]

coverage:
  - id: D1
    description: "Import Plan menu action in File menu with Ctrl+Shift+I shortcut"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_action_exists_in_menu"
        status: pass
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_action_has_shortcut"
        status: pass
    human_judgment: false
  - id: D2
    description: "MainWindowViewModel.import_plan routes PDF to load_plan_from_pdf"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_routes_pdf_to_load_plan_from_pdf"
        status: pass
    human_judgment: false
  - id: D3
    description: "MainWindowViewModel.import_plan routes PNG/JPG/JPEG to load_plan_from_image"
    requirement: PI-02
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_routes_png_to_load_plan_from_image"
        status: pass
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_routes_jpg_to_load_plan_from_image"
        status: pass
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_routes_jpeg_to_load_plan_from_image"
        status: pass
    human_judgment: false
  - id: D4
    description: "File dialog shows correct filter for PDF and image files"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_shows_correct_file_dialog_filter"
        status: pass
    human_judgment: false
  - id: D5
    description: "Cancel dialog does nothing, standalone import works without project"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_cancel_does_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_works_without_project"
        status: pass
    human_judgment: false
  - id: D6
    description: "Error handling emits status message on load failure"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import_ui.py#test_import_plan_error_emits_status_message"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 6: Plan Import UI Summary

**Import Plan menu action with QFileDialog routing PDF/images to PlanViewModel load methods**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-13T17:59:51Z
- **Completed:** 2026-07-13T18:04:24Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Added `import_plan()` slot to MainWindowViewModel with QFileDialog routing by file extension
- Added `Import Plan...` action to File menu with Ctrl+Shift+I shortcut
- Added `plan_vm` property to ProjectViewModel for PlanViewModel access
- 16 automated tests covering unit and integration scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Add import_plan slot to MainWindowViewModel** - `39b57c4` (feat)
2. **Task 2: Add Import Plan action to File menu** - `1ca9613` (feat)
3. **Task 3: Integration test — full import flow** - `235fc1a` (test)

## Files Created/Modified
- `tests/test_plan_import_ui.py` - 16 tests for import UI (unit + integration)
- `src/house_photo_mapper/presentation/viewmodels/main_window_vm.py` - import_plan slot with file dialog routing
- `src/house_photo_mapper/presentation/viewmodels/project_vm.py` - plan_vm property added
- `src/house_photo_mapper/presentation/views/main_window.py` - Import Plan menu action

## Decisions Made
- Standalone import: no project required to import a plan (user can import before creating/opening a project)
- ProjectViewModel.plan_vm property exposes PlanViewModel reference for MainWindowViewModel access
- File dialog filter: "Plans (*.pdf *.png *.jpg *.jpeg);;PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg)"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan import UI entry point complete, plan viewing can proceed
- PlanViewModel.load_plan_from_pdf/load_plan_from_image now callable from UI

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*
