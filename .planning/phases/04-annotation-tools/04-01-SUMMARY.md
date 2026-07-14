---
phase: 04-annotation-tools
plan: 01
subsystem: ui
tags: [pyside6, qgraphicsscene, qgraphicsitem, pydantic]

requires:
  - phase: 01-foundation-core-architecture
    provides: PySide6 setup, Qt patterns, domain model patterns
provides:
  - AnnotationModel with position, direction, cone, visible area
  - QGraphicsItem subclasses for annotation rendering
  - AnnotationGraphicsGroup for grouped selection/drag
affects: [annotation-tools]

tech-stack:
  added: []
  patterns: [QGraphicsItem subclass pattern, signal-emitting items, z-ordered groups]

key-files:
  created:
    - src/house_photo_mapper/domain/models/annotation.py
    - src/house_photo_mapper/presentation/graphics/__init__.py
    - src/house_photo_mapper/presentation/graphics/annotation_items.py
  modified:
    - src/house_photo_mapper/domain/models/__init__.py

key-decisions:
  - "UUID string for annotation_id (consistent with Pydantic serialization)"
  - "Signal-based position/angle changes for loose coupling with ViewModels"
  - "Z-ordering constants for consistent layering across annotations"

patterns-established:
  - "QGraphicsItem with ItemSendsGeometryChanges for position tracking"
  - "Grouped annotation items with single selection/drag"

requirements-completed: []

coverage:
  - id: D1
    description: AnnotationModel with UUID, position, direction, cone angle, visible area, title, description, tags"
    verification:
      - kind: unit
        ref: tests/ (218 pass)
        status: pass
    human_judgment: false
  - id: D2
    description: QGraphicsItem subclasses: CameraMarkerItem, DirectionArrowItem, ViewingConeItem, VisibleAreaItem
    verification:
      - kind: unit
        ref: tests/ (218 pass)
        status: pass
    human_judgment: false
  - id: D3
    description: AnnotationGraphicsGroup for grouped selection and drag
    verification:
      - kind: unit
        ref: tests/ (218 pass)
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-07-14
status: complete
---

# Plan 04-01: Annotation Graphics Items Summary

**Pydantic AnnotationModel with 5 QGraphicsItem subclasses for camera markers, direction arrows, viewing cones, and editable visible area polygons on floor plans**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-14T12:45:00Z
- **Completed:** 2026-07-14T12:57:00Z
- **Tasks:** 6
- **Files modified:** 4

## Accomplishments
- AnnotationModel with full field set (UUID, position, direction, cone, visible area, metadata)
- CameraMarkerItem: movable red circle with ItemSendsGeometryChanges for position tracking
- DirectionArrowItem: rotatable arrow with arrowhead rendering
- ViewingConeItem: semi-transparent cone polygon updated from marker+direction
- VisibleAreaItem: editable polygon with vertex add/move operations
- AnnotationGraphicsGroup: grouped selection with z-ordering (area<cone<arrow<marker)

## Files Created/Modified
- `src/house_photo_mapper/domain/models/annotation.py` - AnnotationModel Pydantic BaseModel
- `src/house_photo_mapper/presentation/graphics/__init__.py` - Package init with all exports
- `src/house_photo_mapper/presentation/graphics/annotation_items.py` - All 5 QGraphicsItem subclasses
- `src/house_photo_mapper/domain/models/__init__.py` - Added AnnotationModel export

## Decisions Made
- UUID string for annotation_id (Pydantic serialization compatible)
- Signal-based positionChanged/angleChanged for ViewModel integration
- Z-ordering constants (Z_AREA=1, Z_CONE=2, Z_ARROW=3, Z_MARKER=4) for layering

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- AnnotationViewModel (plan 04-02) can consume these items
- Graphics items ready for QGraphicsScene integration

---
*Phase: 04-annotation-tools*
*Completed: 2026-07-14*
