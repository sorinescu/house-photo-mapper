---
phase: 02-plan-system
plan: 08
subsystem: ui
tags: [pyside6, qsplitter, planview, planvm, wiring]

# Dependency graph
requires:
  - phase: 02-plan-system
    provides: PlanView, PlanViewModel, PlanSidebar, MainWindowViewModel.import_plan
provides:
  - PlanView as central widget with sidebar navigation
  - PlanViewModel wired to ProjectViewModel via set_plan_vm()
  - Import Plan button in toolbar
affects: [02-plan-system]

# Tech tracking
tech-stack:
  added: []
  patterns: [QSplitter layout, MVVM signal wiring]

key-files:
  created:
    - tests/test_plan_viewport_wiring.py
  modified:
    - src/house_photo_mapper/presentation/views/main_window.py

key-decisions:
  - "PlanViewModel created in MainWindow.__init__() and wired to ProjectViewModel immediately"
  - "QSplitter with sidebar (fixed width) and PlanView (stretch) as central widget"

patterns-established:
  - "PlanView + PlanSidebar in QSplitter is the canonical central widget layout"

requirements-completed: [PI-01, PI-02]

# Coverage metadata
coverage:
  - id: D1
    description: "PlanView is central widget with sidebar navigation in QSplitter layout"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_central_widget_is_splitter"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_plan_view_is_central_child"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_plan_sidebar_is_central_child"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_sidebar_is_left_of_plan_view"
        status: pass
    human_judgment: false
  - id: D2
    description: "PlanViewModel wired to ProjectViewModel via set_plan_vm()"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_plan_vm_exists"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_plan_vm_wired_to_project_vm"
        status: pass
    human_judgment: false
  - id: D3
    description: "Import Plan button in toolbar connected to vm.import_plan"
    requirement: PI-02
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_toolbar_has_import_plan_button"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_import_plan_action_connected_to_vm"
        status: pass
    human_judgment: false
  - id: D4
    description: "Sidebar signals connected to PlanViewModel and PlanView wired for calibration"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_sidebar_signals_connected"
        status: pass
      - kind: unit
        ref: "tests/test_plan_viewport_wiring.py#test_plan_view_connected_to_plan_vm"
        status: pass
    human_judgment: false
  - id: D5
    description: "Human verification of complete plan viewport wiring (visual/functional)"
    verification: []
    human_judgment: true
    rationale: "Visual verification of PlanView displaying as central widget, sidebar showing pages, and import working with PDF/images requires human judgment"

# Metrics
duration: 5min
completed: 2026-07-14
status: complete
---

# Phase 2 Plan 8: PlanView Wiring Summary

**PlanView wired as central widget with sidebar navigation, PlanViewModel connected to ProjectViewModel, and Import Plan button added to toolbar**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-14T05:40:00Z
- **Completed:** 2026-07-14T05:45:17Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 2

## Accomplishments
- PlanView is now the central widget with PlanSidebar in a QSplitter layout
- PlanViewModel created in MainWindow.__init__() and wired to ProjectViewModel via set_plan_vm()
- Import Plan button added to toolbar alongside New/Open/Save
- Sidebar signals (order_changed, floor_changed, itemClicked) connected to PlanViewModel slots
- PlanViewModel.pixmap_ready connected to sidebar thumbnail updates
- PlanView connected to PlanViewModel for calibration click capture

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire PlanView and PlanViewModel into MainWindow** - `493db3a` (feat)
   - Also includes test fix: `51b953c` (test) for RED phase

**Plan metadata:** pending (docs commit)

## Files Created/Modified
- `tests/test_plan_viewport_wiring.py` - New test file verifying all wiring connections
- `src/house_photo_mapper/presentation/views/main_window.py` - PlanView wired as central widget, Import Plan button in toolbar

## Decisions Made
- PlanViewModel created in MainWindow.__init__() rather than lazily — ensures it's always available for import_plan() and signal connections
- QSplitter with fixed sidebar width (stretch=0) and stretching plan view (stretch=1) — sidebar stays compact, plan view fills available space

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan viewport wiring complete, ready for visual verification
- Tests 1 and 2 of UAT marked as pass
- Tests 3-6 still pending (zoom/pan, rotation, floor assignment, persistence)

---
*Phase: 02-plan-system*
*Completed: 2026-07-14*

## Self-Check: PASSED
