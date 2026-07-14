---
status: complete
phase: 04-annotation-tools
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md, 04-05-SUMMARY.md
started: 2026-07-14T15:50:00Z
updated: 2026-07-14T16:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Undo/Redo Annotation Edits
expected: Create an annotation, move marker, Ctrl+Z undoes move, Ctrl+Y redoes move
result: issue
reported: "there is no way to create an annotation - no menu or toolbar items"
severity: major

### 2. Keyboard Shortcuts Active
expected: Ctrl+S saves project, Delete removes selected annotation, arrow keys navigate photos, Ctrl+wheel zooms plan, middle mouse pans plan
result: blocked
blocked_by: prior-phase
reason: "No annotations exist to test Delete or arrow key navigation"

### 3. Annotation Toolbar Tool Selection
expected: Clicking Select/Place Marker/Draw Polygon toolbar buttons switches active tool, toolbar highlights current tool
result: issue
reported: "no such buttons exist"
severity: major

### 4. Properties Panel Metadata Editing
expected: Selecting an annotation shows title/description/tags in properties panel, editing fields updates annotation, title is required (empty title shows error)
result: blocked
blocked_by: prior-phase
reason: "No annotations to select, no toolbar to create them"

### 5. Photo-Annotation Bidirectional Sync
expected: Clicking a photo on the plan highlights it in the photo browser, clicking a photo in the browser highlights its annotation on the plan
result: issue
reported: "there is no way to place a photo on the plan or the other way around"
severity: major

### 6. Annotation Placement Workflow (≤3 clicks)
expected: Select Place Marker tool, click plan to place marker, subsequent steps guide direction/cone/polygon, final step opens metadata form, annotation appears on plan
result: blocked
blocked_by: prior-phase
reason: "No toolbar or menu to initiate placement workflow"

### 7. AnnotationModel Serialization
expected: Create annotation with all fields (title, description, tags, visible area), save project, reload project, annotation data preserved correctly
result: blocked
blocked_by: prior-phase
reason: "No UI to create annotations for serialization test"

### 8. CameraMarkerItem Movable and Selectable
expected: Red circle marker can be clicked to select, dragged to move, position changes emit signal, marker stays within scene bounds
result: blocked
blocked_by: prior-phase
reason: "No UI to create annotations or markers"

**Auto-passed entries (coverage #1602):**

### 9. AnnotationModel with UUID, position, direction, cone, visible area
expected: AnnotationModel with UUID, position, direction, cone, visible area, title, description, tags
result: pass
source: automated
coverage_id: D1-0401

### 10. QGraphicsItem subclasses: CameraMarkerItem, DirectionArrowItem, ViewingConeItem, VisibleAreaItem
expected: All 4 QGraphicsItem subclasses render correctly on QGraphicsScene
result: pass
source: automated
coverage_id: D2-0401

### 11. AnnotationGraphicsGroup for grouped selection and drag
expected: Grouped items select and drag as single unit with correct z-ordering
result: pass
source: automated
coverage_id: D3-0401

### 12. AnnotationViewModel with tool state machine
expected: ToolState transitions: SELECT -> PLACE_MARKER -> SET_DIRECTION -> SET_CONE -> DRAW_POLYGON -> SELECT
result: pass
source: automated
coverage_id: D1-0402

### 13. 5-step creation flow
expected: place_marker -> set_direction -> set_cone_angle -> set_visible_area -> set_metadata completes successfully
result: pass
source: automated
coverage_id: D2-0402

### 14. Floor selection with default from page and metadata form validation
expected: Floor defaults to current page floor, title validation rejects empty strings
result: pass
source: automated
coverage_id: D3-0402

### 15. PlanViewModel integration for page-change annotation sync
expected: AnnotationViewModel receives page change notifications from PlanViewModel
result: pass
source: automated
coverage_id: D4-0402

## Summary

total: 15
passed: 7
issues: 3
pending: 0
skipped: 0
blocked: 5

## Gaps

- truth: "User can create an annotation via menu or toolbar"
  status: failed
  reason: "User reported: there is no way to create an annotation - no menu or toolbar items"
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Annotation toolbar shows Select/Place Marker/Draw Polygon buttons"
  status: failed
  reason: "User reported: no such buttons exist"
  severity: major
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "User can place a photo on a plan and see annotation sync"
  status: failed
  reason: "User reported: there is no way to place a photo on the plan or the other way around"
  severity: major
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
