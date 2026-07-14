---
status: diagnosed
phase: 02-plan-system
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md, 02-06-SUMMARY.md
started: 2026-07-13T21:40:00Z
updated: 2026-07-14T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Multi-Page PDF Import & Navigator
expected: Import a multi-page PDF (5+ pages). All pages appear in the sidebar navigator with thumbnails. Clicking a page switches the viewport to display that page.
result: pass
reported: "PlanView is central widget with QSplitter layout. PlanSidebar left, PlanView right. PlanViewModel wired to ProjectViewModel. Import Plan button in toolbar."
severity: major

### 2. PNG/JPG Image Import
expected: Import a PNG and a JPG plan image. They display with correct orientation (EXIF applied), fit to viewport.
result: pass

### 3. Zoom & Pan Interaction
expected: Ctrl+wheel zoom centers on cursor position. Middle-mouse pan drags plan smoothly at any zoom level. Zoom and pan respond within 100ms with no visible lag.
result: pending

### 4. Rotation
expected: Press R to rotate 90° CW, Shift+R for 90° CCW. Plan rotates in 90° increments around view center.
result: pending

### 5. Floor Assignment & Reorder
expected: Assign floor numbers to plan pages via sidebar dropdown. Drag to reorder pages. Order and floor assignments persist.
result: pending

### 6. Save/Load Persistence
expected: Save project, close, reopen. All plan data persists correctly: pages, order, floor assignments, and calibration restored.
result: pending

## Summary

total: 6
passed: 2
issues: 0
pending: 4
skipped: 0

## Gaps

- truth: "User can import PDF/image plans via toolbar or menu"
  status: resolved
  reason: "MainWindow now creates PlanView as central widget, PlanViewModel wired via set_plan_vm(), Import Plan button added to toolbar."
  severity: major
  test: 1
  root_cause: "PlanView is never instantiated in MainWindow._create_central_widget(). ProjectViewModel.set_plan_vm() is never called, so plan_vm is always None. The import_plan() method correctly checks for None and shows the error. Additionally, the toolbar has no Import button - only New/Open/Save."
  artifacts:
    - path: "src/house_photo_mapper/presentation/views/main_window.py"
      issue: "_create_central_widget() creates placeholder widget, not PlanView. _create_toolbar() missing Import action."
    - path: "src/house_photo_mapper/presentation/viewmodels/main_window_vm.py"
      issue: "import_plan() correctly checks plan_vm but plan_vm is never wired"
    - path: "src/house_photo_mapper/presentation/viewmodels/project_vm.py"
      issue: "set_plan_vm() exists but is never called from application code"
  missing:
    - "Create PlanView instance in _create_central_widget()"
    - "Create PlanViewModel and wire to ProjectViewModel via set_plan_vm()"
    - "Add Import Plan button to toolbar"
    - "Connect PlanView to MainWindow layout (sidebar + plan view)"
  debug_session: ""
  fix_plan: 02-08
