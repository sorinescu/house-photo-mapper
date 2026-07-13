---
phase: 02-plan-system
plan: 01
subsystem: domain-services
tags: [pymupdf, pillow, pydantic, pyside6, processpoolexecutor, display-list, tile-pyramid]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: PySide6 project structure, Pydantic models, infrastructure patterns
provides:
  - PlanModel/PageModel/CalibrationModel Pydantic models with validation
  - PlanRenderer with display list caching for PDF pages
  - PlanRenderer.load_image for PNG/JPG with EXIF orientation
  - TilePyramid with ProcessPoolExecutor for background tile generation
  - PlanGraphicsScene (NoIndex) and PlanGraphicsView (zoom/pan/rotate)
affects: [02-plan-system, 03-photo-system]

# Tech tracking
tech-stack:
  added: [pymupdf, pillow, imageqt]
  patterns: [display-list-caching, process-pool-tile-rendering, exif-orientation-correction, pydantic-validate-assignment]

key-files:
  created:
    - src/house_photo_mapper/domain/models/plan.py
    - src/house_photo_mapper/domain/services/plan_renderer.py
    - src/house_photo_mapper/domain/services/tile_pyramid.py
    - tests/test_plan_import.py
    - tests/test_tile_pyramid.py
  modified:
    - src/house_photo_mapper/domain/services/__init__.py
    - src/house_photo_mapper/infrastructure/qt_patterns.py

key-decisions:
  - "Calibration per-page (not per-project) — architectural plans have different scales per sheet"
  - "ProcessPoolExecutor for PyMuPDF workers — MuPDF not thread-safe, must use processes"
  - "maxtasksperchild=50 prevents worker memory leak from MuPDF global cache"
  - "Display list caching provides 10-50x speedup on re-renders at different zoom levels"
  - "NoIndex mode for PlanGraphicsScene — prevents O(n²) BSP tree degradation with overlapping items"

patterns-established:
  - "Display list caching: page.get_displaylist() reused across renders via dict cache"
  - "Zero-copy QImage: pix.samples buffer wrapped by QImage with _pymupdf_pixmap keep-alive"
  - "ProcessPoolExecutor tile worker: each opens own fitz.Document, returns PNG bytes"
  - "Pydantic ConfigDict(validate_assignment=True, extra='forbid') for all domain models"

requirements-completed: [PI-01, PI-02, PI-07]

coverage:
  - id: D1
    description: "PlanModel, PageModel, CalibrationModel with Pydantic validation, serialization round-trip, per-page calibration"
    requirement: PI-01
    verification:
      - kind: unit
        ref: "tests/test_plan_import.py::TestPlanModel, TestPageModel, TestCalibrationModel"
        status: pass
    human_judgment: false
  - id: D2
    description: "PlanRenderer renders PDF pages via display list caching and loads PNG/JPG with EXIF orientation"
    requirement: PI-02
    verification:
      - kind: unit
        ref: "tests/test_plan_import.py::TestPlanRenderer"
        status: pass
    human_judgment: false
  - id: D3
    description: "TilePyramid generates 512x512 tiles at 4 DPI levels via ProcessPoolExecutor with memory control"
    requirement: PI-07
    verification:
      - kind: unit
        ref: "tests/test_tile_pyramid.py::TestTilePyramid"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 1: Plan System Foundation Summary

**PyMuPDF display-list rendering, Pillow EXIF-aware image loading, Pydantic plan models, and ProcessPoolExecutor tile pyramid for large PDFs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-13T18:14:43Z
- **Completed:** 2026-07-13T18:18:57Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- PlanModel, PageModel, CalibrationModel with Pydantic validation (rotation 0/90/180/270, floor -2..10, calibration per-page)
- PlanRenderer with display list caching (10-50x speedup), zero-copy QImage from pixmap samples
- PlanRenderer.load_image with Pillow EXIF orientation correction via ImageOps.exif_transpose
- TilePyramid generating 512x512 tiles at 72/150/300/600 DPI via ProcessPoolExecutor (maxtasksperchild=50)
- PlanGraphicsScene (NoIndex mode) and PlanGraphicsView (Ctrl+wheel zoom, middle-mouse pan, R rotate) in qt_patterns
- 58 tests passing (40 model/renderer + 18 tile pyramid)

## Task Commits

Each task was committed atomically:

1. **Task 1: PlanModel, PageModel, CalibrationModel** - `ec679ec` (feat) — pre-existing from prior wave
2. **Task 2: PlanRenderer with display list caching** - `a29a6ec` (feat)
3. **Task 3: TilePyramid with ProcessPoolExecutor** - `166de9a` (feat)

## Files Created/Modified
- `src/house_photo_mapper/domain/models/plan.py` — PlanModel, PageModel, CalibrationModel Pydantic models
- `src/house_photo_mapper/domain/services/plan_renderer.py` — PyMuPDF rendering with display list caching, Pillow image loading
- `src/house_photo_mapper/domain/services/tile_pyramid.py` — ProcessPoolExecutor tile generation at 4 DPI levels
- `src/house_photo_mapper/domain/services/__init__.py` — Added PlanRenderer, TilePyramid, TileSpec exports
- `src/house_photo_mapper/infrastructure/qt_patterns.py` — Added PlanGraphicsScene (NoIndex) and PlanGraphicsView
- `tests/test_plan_import.py` — 40 tests for models and renderer
- `tests/test_tile_pyramid.py` — 18 tests for tile pyramid

## Decisions Made
- Calibration per-page (not per-project) — architectural plans have different scales per sheet
- ProcessPoolExecutor for PyMuPDF workers — MuPDF not thread-safe, must use processes
- maxtasksperchild=50 prevents worker memory leak from MuPDF global font/image cache
- Display list caching provides 10-50x speedup on re-renders at different zoom levels
- NoIndex mode for PlanGraphicsScene — prevents O(n²) BSP tree degradation with overlapping items
- Zero-copy QImage from pix.samples with _pymupdf_pixmap keep-alive attribute

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- PlanRenderer tests required `qapp` fixture for QPixmap creation (QGuiApplication requirement) — fixed by adding fixture parameter

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan system foundation complete: models, renderer, tile pyramid ready
- PlanGraphicsScene/View infrastructure ready for viewport implementation
- Ready for Phase 2 remaining plans (calibration, navigation, viewport, persistence)

## Self-Check: PASSED

---
*Phase: 02-plan-system*
*Completed: 2026-07-13*
