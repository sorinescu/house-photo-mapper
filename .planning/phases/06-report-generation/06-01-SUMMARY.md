---
phase: 06-report-generation
plan: 01
subsystem: domain-services
tags: [reportlab, pymupdf, pdf, plan-snippet, camera-overlay, tdd]

# Dependency graph
requires:
  - phase: 05-persistence-performance
    provides: project model persistence, annotation models with position/direction/cone
provides:
  - PlanSnippet service for extracting plan regions centered on camera positions
  - CameraOverlay service for computing cone geometry and drawing camera symbols
  - reportlab dependency for PDF generation
affects: [06-report-generation]

# Tech tracking
tech-stack:
  added: [reportlab>=4.4]
  patterns: [plan-region-extraction, camera-cone-geometry, canvas-overlay-drawing]

key-files:
  created:
    - src/house_photo_mapper/domain/services/plan_snippet.py
    - src/house_photo_mapper/domain/services/camera_overlay.py
    - tests/test_plan_snippet.py
    - tests/test_camera_overlay.py
  modified:
    - pyproject.toml

key-decisions:
  - "PlanSnippet uses PyMuPDF get_pixmap(clip=...) for region rendering with scene-to-PDF coordinate conversion"
  - "CameraOverlay is stateless with all static methods, separating geometry computation from canvas drawing"
  - "Rotation handling skips clipping for rotated pages — PyMuPDF rotates output automatically"

patterns-established:
  - "Plan region extraction: scene coords → PDF points via pixels_per_meter, clip & page.rect for bounds"
  - "Camera overlay: stateless service with compute_cone_vertices + draw_camera_overlay separation"

requirements-completed: [RG-03, RG-04]

coverage:
  - id: D1
    description: "PlanSnippet extracts plan regions centered on camera positions with bounds clamping and rotation handling"
    requirement: RG-03
    verification:
      - kind: unit
        ref: "tests/test_plan_snippet.py#test_render_basic_region"
        status: pass
      - kind: unit
        ref: "tests/test_plan_snippet.py#test_clamp_to_bounds"
        status: pass
      - kind: unit
        ref: "tests/test_plan_snippet.py#test_handle_rotation"
        status: pass
    human_judgment: false
  - id: D2
    description: "CameraOverlay computes cone vertices and draws camera symbols on ReportLab canvas"
    requirement: RG-04
    verification:
      - kind: unit
        ref: "tests/test_camera_overlay.py#test_compute_cone_vertices_zero_angle"
        status: pass
      - kind: unit
        ref: "tests/test_camera_overlay.py#test_compute_cone_vertices_ninety_degrees"
        status: pass
      - kind: unit
        ref: "tests/test_camera_overlay.py#test_draw_camera_overlay"
        status: pass
    human_judgment: false

# Metrics
duration: 5min
completed: 2026-07-15
status: complete
---

# Phase 6 Plan 01: Report Generation Services Summary

**PlanSnippet region extraction via PyMuPDF clip rendering and CameraOverlay cone geometry with ReportLab canvas drawing**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-15T18:31:56Z
- **Completed:** 2026-07-15T18:37:18Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Installed reportlab>=4.4 (v5.0.0) as project dependency for PDF generation
- Created PlanSnippet service with extract_plan_snippet() using PyMuPDF get_pixmap(clip=...) for region rendering
- Created CameraOverlay service with compute_cone_vertices() geometry computation and draw_camera_overlay() canvas drawing
- All 9 tests passing (4 PlanSnippet, 5 CameraOverlay)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install reportlab and create test scaffolds** - `c90210f` (feat)
2. **Task 2: Implement PlanSnippet service** - `fc4c724` (test — RED gate) + `c90210f` (feat — GREEN gate)
3. **Task 3: Implement CameraOverlay service** - `290dd8a` (test — RED gate) + `c90210f` (feat — GREEN gate)

## Files Created/Modified
- `src/house_photo_mapper/domain/services/plan_snippet.py` - PlanSnippet dataclass and extract_plan_snippet() function
- `src/house_photo_mapper/domain/services/camera_overlay.py` - CameraOverlay class with static methods for cone geometry and canvas drawing
- `tests/test_plan_snippet.py` - 4 tests: render, clamp, rotation, dataclass
- `tests/test_camera_overlay.py` - 5 tests: cone vertices, invalid inputs, canvas drawing
- `pyproject.toml` - Added reportlab>=4.4 dependency
- `uv.lock` - Updated lockfile

## Decisions Made
- PlanSnippet uses scene-to-PDF coordinate conversion: `(center_x / pixels_per_meter) * 72` for 72 DPI base
- Rotation handling skips clip intersection for rotated pages — PyMuPDF rotates output internally
- CameraOverlay separates geometry computation (compute_cone_vertices) from drawing (draw_camera_overlay) for testability
- CameraOverlay uses HexColor with alpha suffix for semi-transparent cone fill (#DC28281A = ~10% opacity)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PlanSnippet and CameraOverlay services ready for ReportGeneratorService (Plan 02)
- reportlab dependency installed and verified (v5.0.0)
- All verification commands pass

## Self-Check: PASSED

All key files exist on disk. All 3 task commits verified in git log. All 9 tests pass. reportlab v5.0.0 importable.

---
*Phase: 06-report-generation*
*Completed: 2026-07-15*
