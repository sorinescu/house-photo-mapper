---
phase: 02-plan-system
plan: 05
subsystem: persistence
tags: [pydantic, json, atomic-write, plan-model, calibration, viewmodel]

# Dependency graph
requires:
  - phase: 02-01
    provides: PlanModel, PageModel, CalibrationModel domain models
  - phase: 02-04
    provides: CalibrationService, CalibrationViewModel, PlanViewModel
provides:
  - PlanModel persistence to plans.json with atomic write
  - ProjectViewModel plan save/load integration
  - PlanViewModel UI sync signals (pages_changed, page_changed, calibration_changed)
  - PlanRenderer request_page_render for viewport
affects: [03-photo-system, 04-annotations, 06-export]

# Tech tracking
tech-stack:
  added: []
  patterns: [atomic-write-tmp-rename, pydantic-private-attr, plan-vm-signal-sync]

key-files:
  created: [tests/test_persistence.py]
  modified:
    - src/house_photo_mapper/domain/services/persistence.py
    - src/house_photo_mapper/domain/models/project.py
    - src/house_photo_mapper/presentation/viewmodels/plan_vm.py
    - src/house_photo_mapper/presentation/viewmodels/project_vm.py

key-decisions:
  - "Used Pydantic PrivateAttr for ProjectModel._dirty instead of dataclasses.field"
  - "PlanViewModel.set_plan_model emits all three signals (pages_changed, page_changed, calibration_changed) for full UI sync"
  - "set_page now emits calibration_changed for newly active page"

patterns-established:
  - "Atomic write pattern: .tmp → rename for plans.json"
  - "PlanViewModel UI sync: set_plan_model emits pages_changed + page_changed + calibration_changed"

requirements-completed: [PI-01, PI-02, PI-03, PI-07]

coverage:
  - id: D1
    description: "PlanModel saves/loads atomically to plans.json via PersistenceService"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_persistence.py::TestPlanModelPersistence::test_plan_model_persistence"
        status: pass
      - kind: unit
        ref: "tests/test_persistence.py::TestPlanModelPersistence::test_atomic_write"
        status: pass
    human_judgment: false
  - id: D2
    description: "CalibrationModel round-trips correctly through JSON serialization"
    requirement: PI-02
    verification:
      - kind: unit
        ref: "tests/test_persistence.py::TestPlanModelPersistence::test_calibration_round_trip"
        status: pass
    human_judgment: false
  - id: D3
    description: "ProjectViewModel saves/loads plans.json and injects PlanModel into PlanViewModel"
    requirement: PI-03
    verification:
      - kind: integration
        ref: "tests/test_persistence.py::TestProjectPlanIntegration::test_project_save_includes_plans"
        status: pass
      - kind: integration
        ref: "tests/test_persistence.py::TestProjectPlanIntegration::test_project_load_restores_plan_model"
        status: pass
    human_judgment: false
  - id: D4
    description: "PlanViewModel emits pages_changed, page_changed, calibration_changed on load"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_persistence.py::TestPlanUISyncOnLoad::test_set_plan_model_emits_pages_changed"
        status: pass
      - kind: unit
        ref: "tests/test_persistence.py::TestPlanUISyncOnLoad::test_set_plan_model_emits_calibration_changed"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full save/load cycle with PlanModel injection and UI sync"
    requirement: PI-03
    verification:
      - kind: integration
        ref: "tests/test_persistence.py::TestPlanUISyncOnLoad::test_full_save_load_ui_sync"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 5: PlanModel Persistence Summary

**PlanModel persistence to plans.json with atomic write, ProjectViewModel integration, and PlanViewModel UI sync signals**

## Performance

- **Duration:** 9 min
- **Started:** 2026-07-13T17:05:15Z
- **Completed:** 2026-07-13T17:14:32Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- PersistenceService.save_plan_model/load_plan_model with atomic .tmp → rename write
- ProjectViewModel.save_project saves both .hpmpj and plans.json; open_project loads both
- PlanViewModel.set_plan_model emits pages_changed, page_changed, calibration_changed for full UI sync
- PlanViewModel.request_page_render renders pages via PlanRenderer and emits pixmap_ready
- Fixed pre-existing ProjectModel._dirty bug (dataclasses.field → Pydantic PrivateAttr)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend PersistenceService with PlanModel save/load** - `6e17baa` (feat)
2. **Task 2: Integrate PlanModel persistence with ViewModels** - `75470d0` (feat)
3. **Task 3: PlanViewModel UI sync signals on load** - `a4fee58` (feat)

## Files Created/Modified
- `tests/test_persistence.py` - 17 tests for persistence round-trip, integration, UI sync
- `src/house_photo_mapper/domain/services/persistence.py` - Added save_plan_model/load_plan_model
- `src/house_photo_mapper/domain/models/project.py` - Fixed _dirty to use PrivateAttr
- `src/house_photo_mapper/presentation/viewmodels/plan_vm.py` - Added set_plan_model, get_plan_model, request_page_render, calibration_changed in set_page
- `src/house_photo_mapper/presentation/viewmodels/project_vm.py` - Added plan VM coordination, plan save/load in save/open

## Decisions Made
- Used Pydantic PrivateAttr for ProjectModel._dirty — dataclasses.field doesn't work with Pydantic BaseModel
- PlanViewModel.set_plan_model emits all three signals for complete UI sync on project load
- set_page now emits calibration_changed for newly active page (was missing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed ProjectModel._dirty using dataclasses.field**
- **Found during:** Task 2 (integration tests)
- **Issue:** ProjectModel used `dataclasses.field(default=False, init=False, repr=False)` but it's a Pydantic BaseModel — Pydantic's smart_deepcopy fails on mappingproxy from dataclass field
- **Fix:** Changed to `PrivateAttr(default=False)` from pydantic
- **Files modified:** src/house_photo_mapper/domain/models/project.py
- **Verification:** All tests pass including create_empty()
- **Committed in:** 75470d0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Bug fix essential for ProjectModel to function. No scope creep.

## Issues Encountered
None beyond the auto-fixed ProjectModel bug.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PlanModel persistence fully functional for save/load cycle
- Ready for Phase 3 (Photo System) to add photo persistence
- Ready for Phase 4 (Annotations) to add annotation persistence
- Phase 6 (Export) can reference plans.json for report generation

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*

## Self-Check: PASSED
