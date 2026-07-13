---
phase: 02-plan-system
plan: 03
subsystem: presentation
tags: [pyside6, qlistwidget, drag-drop, combo-box, thumbnail, sidebar, viewmodel-integration]

# Dependency graph
requires:
  - phase: 02-plan-system
    plan: 01
    provides: PlanModel, PageModel, PlanRenderer
  - phase: 02-plan-system
    plan: 02
    provides: PlanViewModel, PlanView, PlanGraphicsScene/View
provides:
  - PlanSidebar widget with thumbnail display, drag-reorder, and floor assignment
  - PlanViewModel sidebar integration slots for page switching and persistence
  - Integration tests for sidebar-ViewModel signal connections
affects: [02-plan-system, 04-annotation]

# Tech tracking
tech-stack:
  added: []
  patterns: [qlistwidget-internalmove, combo-box-item-widget, sidebar-viewmodel-integration]

key-files:
  created:
    - src/house_photo_mapper/presentation/views/plan_sidebar.py
    - tests/test_plan_sidebar.py
  modified:
    - src/house_photo_mapper/presentation/viewmodels/plan_vm.py

key-decisions:
  - "PlanSidebar uses QListWidget.InternalMove for native drag-reorder"
  - "Floor combo box per item: -2 (Basement 2) to 10 (Floor 10)"
  - "Sidebar signals: order_changed(list[dict]), floor_changed(int, int)"
  - "ViewModel slots: on_sidebar_order_changed, on_sidebar_floor_changed, on_sidebar_page_clicked"
  - "ViewModel emits pages_reordered and floor_changed for UI sync"

patterns-established:
  - "QListWidget.InternalMove for drag-reorder: native, accessible, keyboard support"
  - "QComboBox as item widget for per-item configuration"
  - "Sidebar-ViewModel integration via Qt signals/slots"

requirements-completed: [PI-03, PI-06]

coverage:
  - id: D1
    description: "PlanSidebar widget with thumbnail display, drag-reorder, and floor assignment"
    requirement: PI-03
    verification:
      - kind: unit
        ref: "tests/test_plan_sidebar.py::TestPlanSidebar::test_plan_sidebar_drag_reorder"
        status: pass
    human_judgment: false
  - id: D2
    description: "PlanViewModel sidebar integration for page switching and floor updates"
    requirement: PI-06
    verification:
      - kind: unit
        ref: "tests/test_plan_sidebar.py::TestPlanSidebarIntegration::test_sidebar_viewmodel_integration"
        status: pass
    human_judgment: false

# Metrics
duration: 5min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 3: Plan Sidebar Summary

**QListWidget sidebar with thumbnail display, drag-reorder, floor assignment combos, and full PlanViewModel integration**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-13T18:29:32Z
- **Completed:** 2026-07-13T18:34:45Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- PlanSidebar widget with IconMode, InternalMove drag-drop, 120x120 thumbnails
- Floor combo box per page: -2 (Basement 2) to 10 (Floor 10) with signal emission
- Drag-reorder emits order_changed with full page list in new order
- PlanViewModel integration: on_sidebar_order_changed, on_sidebar_floor_changed, on_sidebar_page_clicked
- pages_reordered and floor_changed signals for UI synchronization
- 18 tests passing: sidebar configuration, thumbnails, floor combos, drag-reorder, integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PlanSidebar widget** - `e0a87be` (test)
2. **Task 2: Integrate PlanSidebar with PlanViewModel** - `17ffd3b` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/house_photo_mapper/presentation/views/plan_sidebar.py` - PlanSidebar widget with thumbnails, drag-reorder, floor combos
- `src/house_photo_mapper/presentation/viewmodels/plan_vm.py` - Extended with sidebar integration slots and signals
- `tests/test_plan_sidebar.py` - 18 tests covering sidebar functionality and ViewModel integration

## Decisions Made
- PlanSidebar uses QListWidget.InternalMove for native drag-reorder (RESEARCH.md Pattern 6)
- Floor combo box stores page_num in UserRole data for signal emission
- ViewModel slots follow Qt naming convention: on_sidebar_[event]
- pages property exposes sorted pages for sidebar initial population

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] PlanView and viewport tests not committed**
- **Found during:** Task 1
- **Issue:** plan_view.py and test_plan_viewport.py existed but were not committed from previous wave
- **Fix:** Committed missing files with proper commit message
- **Files modified:** src/house_photo_mapper/presentation/views/plan_view.py, tests/test_plan_viewport.py
- **Verification:** All tests pass
- **Committed in:** 5a35747

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** No scope creep. All requirements PI-03, PI-06 verified satisfied.

## Issues Encountered
- None - all verification criteria pass

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan sidebar complete: thumbnails, drag-reorder, floor assignment
- PlanViewModel ready for sidebar integration (all slots implemented)
- Ready for Phase 2 remaining plans (calibration, persistence)
- Ready for Phase 4 annotation system (sidebar integration points established)

## Self-Check: PASSED

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*
