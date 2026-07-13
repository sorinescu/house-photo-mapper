---
phase: 02-plan-system
plan: 02
subsystem: presentation
tags: [pyside6, qgraphicsscene, qgraphicsview, anchorundermouse, noindex, zoom, pan, rotate]

# Dependency graph
requires:
  - phase: 02-plan-system
    plan: 01
    provides: PlanGraphicsScene/View infrastructure in qt_patterns.py, PlanRenderer, PlanModel
provides:
  - PlanGraphicsScene with NoIndex mode (O(1) add/move/remove)
  - PlanGraphicsView with Ctrl+wheel zoom (cursor-centered), middle-mouse pan, R/Shift+R rotate
  - PlanViewModel coordinating page display, viewport state, calibration signals
  - PlanView widget integrating scene, view, and ViewModel with signal connections
  - 28 viewport tests covering scene config, zoom, pan, rotate, ViewModel signals, integration
affects: [02-plan-system, 03-photo-system, 04-annotation]

# Tech tracking
tech-stack:
  added: []
  patterns: [anchorundermouse-first-wheel-fix, noindex-bsp-tree-avoidance, scale-compensated-pan, rotate-view-not-scene]

key-files:
  created:
    - src/house_photo_mapper/presentation/viewmodels/plan_vm.py
    - src/house_photo_mapper/presentation/views/plan_view.py
    - tests/test_plan_viewport.py
  modified:
    - src/house_photo_mapper/infrastructure/qt_patterns.py

key-decisions:
  - "NoIndex mode for PlanGraphicsScene — prevents O(n²) BSP tree degradation with overlapping items"
  - "AnchorUnderMouse + viewport.mouseTracking — fixes first-wheel jump (Pitfall 5)"
  - "Middle-mouse translate() with scale compensation — works without scrollbars at any zoom level"
  - "R rotates view (not scene) — scene items rotate with view transform"
  - "PlanView exposes view() getter — CalibrationDialog installs event filter for click capture"

patterns-established:
  - "NoIndex scene: O(1) add/move/remove for plan pixmap + annotations"
  - "AnchorUnderMouse: zoom always centers on cursor, never jumps"
  - "Scale-compensated pan: translate(delta/m11, delta/m22) for uniform zoom"
  - "ViewModel signals: pixmap_ready, zoom_changed, rotation_changed, calibration_changed"

requirements-completed: [PI-03, PI-04, PI-05, PI-06]

coverage:
  - id: D1
    description: "PlanGraphicsScene with NoIndex mode — prevents BSP tree O(n²) degradation"
    requirement: PI-03
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanGraphicsScene::test_scene_uses_no_index"
        status: pass
    human_judgment: false
  - id: D2
    description: "PlanGraphicsView zoom (Ctrl+wheel) centers on mouse cursor via AnchorUnderMouse"
    requirement: PI-04
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanGraphicsView::test_wheel_event_zoom_in"
        status: pass
    human_judgment: false
  - id: D3
    description: "PlanGraphicsView pan (middle mouse) translates scene with scale compensation"
    requirement: PI-05
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanGraphicsView::test_mouse_move_pans_scene"
        status: pass
    human_judgment: false
  - id: D4
    description: "PlanGraphicsView rotate (R/Shift+R) rotates view 90° CW/CCW"
    requirement: PI-06
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanGraphicsView::test_key_press_r_rotates_90_cw"
        status: pass
    human_judgment: false
  - id: D5
    description: "PlanViewModel emits pixmap_ready on page change, tracks zoom/rotation/calibration"
    requirement: PI-03
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanViewModel::test_set_page_emits_pixmap_ready"
        status: pass
    human_judgment: false
  - id: D6
    description: "PlanView integrates scene/view/viewmodel, fits pixmap on first load, syncs zoom/rotation"
    requirement: PI-03
    verification:
      - kind: unit
        ref: "tests/test_plan_viewport.py::TestPlanViewIntegration::test_plan_view_fit_in_view_on_first_pixmap"
        status: pass
    human_judgment: false

# Metrics
duration: 1min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 2: Plan Viewport Summary

**NoIndex QGraphicsScene, AnchorUnderMouse zoom, middle-mouse pan, R/Shift+R rotate — all with 28 passing viewport tests**

## Performance

- **Duration:** 1 min (verification only — implementation completed in 02-01)
- **Started:** 2026-07-13T18:25:27Z
- **Completed:** 2026-07-13T18:26:30Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- PlanGraphicsScene uses NoIndex mode — O(1) add/move/remove for plan pixmap + annotations
- PlanGraphicsView handles Ctrl+wheel zoom (cursor-centered via AnchorUnderMouse + mouseTracking), middle-mouse pan (scale-compensated translate), R/Shift+R rotate (90° increments)
- PlanViewModel coordinates page display via PlanRenderer, emits pixmap_ready/zoom_changed/rotation_changed/calibration_changed signals
- PlanView widget integrates scene/view/viewmodel, fits pixmap on first load, syncs zoom/rotation, exposes view() for CalibrationDialog
- 28 tests passing: scene config, zoom in/out, pan, rotate, ViewModel signals, PlanView integration

## Task Commits

Each task was committed atomically:

1. **Task 1: PlanGraphicsScene and PlanGraphicsView** - `166de9a` (feat) — completed in 02-01
2. **Task 2: PlanViewModel** - `ec679ec` (feat) — completed in 02-01
3. **Task 3: PlanView** - `ec679ec` (feat) — completed in 02-01

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/house_photo_mapper/infrastructure/qt_patterns.py` — Extended with PlanGraphicsScene (NoIndex) and PlanGraphicsView (zoom/pan/rotate)
- `src/house_photo_mapper/presentation/viewmodels/plan_vm.py` — PlanViewModel with page/zoom/rotation/calibration signals
- `src/house_photo_mapper/presentation/views/plan_view.py` — PlanView widget integrating scene, view, and ViewModel
- `tests/test_plan_viewport.py` — 28 tests covering all viewport functionality

## Decisions Made
- NoIndex mode for PlanGraphicsScene — prevents O(n²) BSP tree degradation with overlapping items
- AnchorUnderMouse + viewport.mouseTracking — fixes first-wheel jump (RESEARCH.md Pitfall 5)
- Middle-mouse translate() with scale compensation — works without scrollbars at any zoom level
- R rotates view (not scene) — scene items rotate with view transform
- PlanView exposes view() getter — CalibrationDialog installs event filter for click capture

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] All implementation completed in 02-01 wave**
- **Found during:** Task 1-3
- **Issue:** Plan 02-02 specified creating PlanGraphicsScene/View, PlanViewModel, PlanView — but all were already implemented in 02-01 as part of the plan system foundation wave
- **Fix:** Verified existing implementation meets all requirements; all 28 tests pass
- **Files verified:** qt_patterns.py, plan_vm.py, plan_view.py, test_plan_viewport.py
- **Verification:** uv run pytest tests/test_plan_viewport.py -xvs (28 passed)
- **Committed in:** ec679ec, a29a6ec, 166de9a (02-01 wave)

---

**Total deviations:** 1 auto-fixed (1 missing critical — implementation pre-existed)
**Impact on plan:** No scope creep. All requirements PI-03 through PI-06 verified satisfied.

## Issues Encountered
- None — all verification criteria pass

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan viewport complete: NoIndex scene, AnchorUnderMouse zoom, middle-mouse pan, R rotate
- PlanViewModel ready for sidebar integration (pages_changed signal)
- PlanView ready for calibration click capture (event filter on view())
- Ready for Phase 2 remaining plans (sidebar, calibration, persistence)

## Self-Check: PASSED

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*
