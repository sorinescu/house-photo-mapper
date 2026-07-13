---
phase: 02-plan-system
plan: 04
subsystem: calibration
tags: [pyside6, qdialog, calibration, two-point-verification, scene-coordinates]

# Dependency graph
requires:
  - phase: 02-01
    provides: PlanModel, PageModel, CalibrationModel domain models
  - phase: 02-02
    provides: PlanGraphicsView with mapToScene for click capture
provides:
  - CalibrationService with ppm computation and two-point verification
  - CalibrationViewModel managing 5-step wizard state
  - CalibrationDialog with guided workflow
  - Integration with PlanViewModel for per-page calibration storage
affects: [03-photo-system, 04-annotations, 06-export]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-point-verification, scene-coordinate-ppm, event-filter-click-capture]

key-files:
  created:
    - src/house_photo_mapper/domain/services/calibration.py
    - src/house_photo_mapper/presentation/viewmodels/calibration_vm.py
    - src/house_photo_mapper/presentation/views/calibration_dialog.py
    - tests/test_calibration.py
  modified: []

key-decisions:
  - "CalibrationService uses static methods (stateless) for testability"
  - "Points stored as [x, y] lists in CalibrationModel for JSON serialization"
  - "Verification tolerance ≤2% per industry standard (RESEARCH.md Pitfall 3)"
  - "ppm stored in SCENE coordinates (invariant to view zoom/pan/rotate)"

patterns-established:
  - "Two-point calibration: enter spec → click point1 → click point2 → verify with second dimension"
  - "Event filter click capture on PlanGraphicsView for scene coordinate mapping"
  - "Unit conversion combo (meters/feet/inches) in CalibrationDialog"

requirements-completed: [PI-07]

coverage:
  - id: D1
    description: "CalibrationService computes ppm from two scene points and known distance"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationService::test_calibrate_basic"
        status: pass
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationService::test_calibrate_zero_distance"
        status: pass
    human_judgment: false
  - id: D2
    description: "Verification passes at 1.9% error, fails at 2.1% error"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationService::test_verify_pass"
        status: pass
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationService::test_verify_fail"
        status: pass
    human_judgment: false
  - id: D3
    description: "CalibrationDialog 5-step wizard with unit conversion"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationDialog::test_wizard_step_progression"
        status: pass
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationDialog::test_unit_conversion"
        status: pass
    human_judgment: false
  - id: D4
    description: "Click capture via event filter returns scene coordinates"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_calibration.py::TestCalibrationDialog::test_click_capture_scene_coords"
        status: pass
    human_judgment: false
  - id: D5
    description: "PlanViewModel launches calibration and stores result per-page"
    requirement: PI-07
    verification:
      - kind: integration
        ref: "tests/test_calibration.py::TestCalibrationIntegration::test_calibration_integration"
        status: pass
    human_judgment: false

duration: 0min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 4: Scale Calibration Summary

**Specification-based scale calibration with two-point verification: user enters known dimension, clicks two endpoints, software computes pixels-per-meter in scene coordinates; second dimension verification enforces ≤2% error tolerance**

## Performance

- **Duration:** 0 min (closed out from prior session — all work already committed)
- **Completed:** 2026-07-13
- **Tasks:** 3
- **Files modified:** 4
- **Tests:** 38 passing

## Accomplishments
- CalibrationService with calibrate() and verify() static methods
- CalibrationModel stores ppm, verified flag, reference points in scene coordinates
- CalibrationViewModel manages 5-step wizard state machine
- CalibrationDialog with unit combo (meters/feet/inches) and event filter click capture
- Integration with PlanViewModel for per-page calibration storage
- Verification enforces ≤2% error tolerance on second dimension

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CalibrationService with ppm computation and verification** - `4db3f05` (test)
2. **Task 2: Create CalibrationViewModel and CalibrationDialog** - `de96746` (feat)
3. **Task 3: Integrate calibration with PlanViewModel and PlanGraphicsView** - `dfcfe3e` (feat)

## Files Created/Modified
- `src/house_photo_mapper/domain/services/calibration.py` - CalibrationService with calibrate/verify
- `src/house_photo_mapper/presentation/viewmodels/calibration_vm.py` - CalibrationViewModel wizard
- `src/house_photo_mapper/presentation/views/calibration_dialog.py` - CalibrationDialog UI
- `tests/test_calibration.py` - 38 tests for service, dialog, and integration

## Decisions Made
- CalibrationService uses static methods (stateless) for testability
- Points stored as [x, y] lists in CalibrationModel for JSON serialization
- Verification tolerance ≤2% per industry standard
- ppm stored in SCENE coordinates (invariant to view zoom/pan/rotate)

## Deviations from Plan
None — all 3 tasks completed as specified.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Calibration service ready for photo system integration (Phase 3)
- Per-page calibration stored in PlanModel for annotation scaling (Phase 4)
- ppm in scene coordinates ready for export calculations (Phase 6)

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*

## Self-Check: PASSED
