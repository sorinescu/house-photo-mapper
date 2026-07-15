---
phase: 04-annotation-tools
plan: 07
subsystem: ui
tags: [annotation, qgraphicsitem, grouping, color-picker, undo-redo, pyqt]

# Dependency graph
requires:
  - phase: 02-plan-system
    provides: PlanViewModel and plan viewport infrastructure
  - phase: 03-photo-management
    provides: PhotoViewModel and photo browser
provides:
  - Annotation grouping system (marker + arrow + cone + rectangle as single unit)
  - Per-annotation color selection with persistent color field
  - Interactive cone rotation via mouse drag
  - Resizable rectangle with grip handles
  - Undo/redo commands with merge compression for move/resize/rotate
affects: [06-report-generation, 07-final-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [QGraphicsItemGroup, GripItem resize handles, mergeable QUndoCommand]

key-files:
  created: []
  modified:
    - src/house_photo_mapper/domain/models/annotation.py
    - src/house_photo_mapper/presentation/graphics/annotation_items.py
    - src/house_photo_mapper/presentation/viewmodels/annotation_vm.py
    - src/house_photo_mapper/presentation/views/annotation_toolbar.py
    - src/house_photo_mapper/presentation/views/annotation_properties_panel.py
    - src/house_photo_mapper/presentation/views/main_window.py
    - src/house_photo_mapper/presentation/commands.py
    - src/house_photo_mapper/infrastructure/qt_patterns.py

key-decisions:
  - "VisibleAreaItem changed from QGraphicsPolygonItem to QGraphicsRectItem for resize handles"
  - "GripItem at 8 positions (4 corners + 4 edge midpoints) for rectangle resize"
  - "Cone rotation via SET_CONE tool: click nearest marker, drag to rotate cone direction"
  - "Color stored as hex string in AnnotationModel with default #DC2828"

patterns-established:
  - "AnnotationGraphicsGroup: groups marker, arrow, cone, rectangle with shared annotation_id"
  - "Mergeable QUndoCommand: mergeWith() compresses consecutive move/resize/rotate operations"

requirements-completed: []

coverage:
  - id: D1
    description: Annotation grouping - marker, cone, and rectangle created as single group on placement"
    verification:
      - kind: unit
        ref: tests/unit/test_qt_patterns.py
        status: pass
    human_judgment: false
  - id: D2
    description: Per-annotation color selection with color picker in properties panel"
    verification:
      - kind: unit
        ref: tests/unit/test_project_model.py
        status: pass
    human_judgment: false
  - id: D3
    description: Interactive cone rotation via mouse drag with SET_CONE tool"
    verification: []
    human_judgment: true
    rationale: "Cone rotation requires visual verification of mouse interaction and geometry updates"
  - id: D4
    description: Resizable rectangle with grip handles at corners and edges"
    verification: []
    human_judgment: true
    rationale: "Grip handle dragging and resize behavior requires visual verification"
  - id: D5
    description: Undo/redo commands with merge compression for move, resize, rotate"
    verification:
      - kind: unit
        ref: tests/unit/test_qt_patterns.py
        status: pass
    human_judgment: false

# Metrics
duration: 13min
completed: 2026-07-15
status: complete
---

# Phase 04 Plan 07: Annotation Grouping & Interactive Tools Summary

**Grouped annotation system with per-annotation colors, interactive cone rotation, and resizable rectangle with grip handles**

## Performance

- **Duration:** 13 min
- **Started:** 2026-07-15T06:47:01Z
- **Completed:** 2026-07-15T07:00:40Z
- **Tasks:** 8
- **Files modified:** 8

## Accomplishments
- Replaced freeform polygon VisibleAreaItem with QGraphicsRectItem supporting 8 grip handles for resize
- Created AnnotationGraphicsGroup storing annotation_id for linkage to data model
- Added color field to AnnotationModel with hex color string (default #DC2828)
- Added ColorButton widget and color picker to AnnotationPropertiesPanel
- Implemented SET_CONE tool state with mouse drag cone rotation around marker
- Created MoveMarkerCommand, ResizeRectangleCommand, RotateConeCommand with mergeWith compression
- Updated PlaceAnnotationCommand and DeleteAnnotationCommand for grouped items
- Wired color_changed signal from panel through ViewModel to graphics group

## Task Commits

Each task was committed atomically:

1. **Task 1-8: Core implementation** - `be1d668` (feat)
2. **Fix: Wire color picker and menu actions** - `4268cea` (fix)
3. **Fix: Import errors and export color** - `98c6e7d` (fix)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/house_photo_mapper/domain/models/annotation.py` - Added color field with default #DC2828
- `src/house_photo_mapper/presentation/graphics/annotation_items.py` - GripItem, resizable VisibleAreaItem, color support on all items
- `src/house_photo_mapper/presentation/viewmodels/annotation_vm.py` - Removed DRAW_POLYGON, added update_annotation_color
- `src/house_photo_mapper/presentation/views/annotation_toolbar.py` - Replaced Draw Polygon with Set Cone button
- `src/house_photo_mapper/presentation/views/annotation_properties_panel.py` - Added ColorButton and color picker
- `src/house_photo_mapper/presentation/views/main_window.py` - Wired color signal, updated menu actions
- `src/house_photo_mapper/presentation/commands.py` - Added MoveMarker, ResizeRectangle, RotateCone with merge
- `src/house_photo_mapper/infrastructure/qt_patterns.py` - PlanGraphicsView creates full groups, SET_CONE handler

## Decisions Made
- VisibleAreaItem changed from QGraphicsPolygonItem to QGraphicsRectItem for resize handles
- GripItem placed at 8 positions (4 corners + 4 edge midpoints) for intuitive resize
- Cone rotation uses nearest-marker lookup for click-to-rotate interaction
- Color stored as hex string in AnnotationModel for JSON serialization compatibility
- Mergeable QUndoCommand pattern for smooth undo/redo of drag operations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing structlog API incompatibility in `_scan_for_recovery` causes test failures in MainWindow tests (not related to this plan)

## Known Stubs
- None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Annotation system fully functional with grouped items, colors, and interactive tools
- Ready for report generation phase to use annotation data
- Color persistence in project JSON verified via serialization roundtrip test

---
*Phase: 04-annotation-tools*
*Completed: 2026-07-15*

## Self-Check: PASSED

- All 8 key files exist on disk
- All 3 commits (be1d668, 4268cea, 98c6e7d) found in git log
- SUMMARY.md exists at .planning/phases/04-annotation-tools/04-07-SUMMARY.md
