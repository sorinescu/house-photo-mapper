---
status: testing
phase: 03-photo-system
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md
started: 2026-07-14T10:45:00Z
updated: 2026-07-14T10:45:00Z
---

## Current Test

number: 4
name: Duplicate Detection
expected: |
  Import two copies of the same image. Both appear in the browser but are marked with a "[Duplicate: dup_X]" badge.
awaiting: user response

## Tests

### 1. Photo Import via Drag-Drop
expected: Drag an image file onto the app window. Photo appears in the photo browser panel with thumbnail.
result: fixed
reported: "The status bar says 'Imported 1 photo' but nothing is visible. Dropping another image afterwards doesn't do anything, the status bar remains the same."
severity: major
fix: "Delegated import to PhotoViewModel which emits photo_added signal to update browser"

### 2. Import Photos Menu
expected: Click File > Import Photos (Ctrl+Shift+P), select image files. Photos appear in the photo browser.
result: fixed
reported: "Even though there is an 'Import photos' item in the File menu, it doesn't allow any photo to be selected in the instantiated file browser."
severity: major
fix: "Changed to file dialog for selecting individual images"

### 3. Toolbar Import Photos Button
expected: There is an "Import Photos" button in the toolbar for quick access.
result: fixed
reported: "There should be an 'Import photos' item in the toolbar."
severity: major
fix: "Added Import Photos button to toolbar"

### 4. Thumbnail Generation
expected: Import several photos. Thumbnails appear as actual images, not grey boxes.
result: fixed
reported: "The thumbnails are blank (solid grey boxes)."
severity: major
fix: "Moved QPixmap creation to main thread - QPixmap operations must happen on main thread in Qt"

### 5. EXIF Metadata Display
expected: Click on an imported photo in the browser. The metadata panel below shows filename, dimensions, file size, and camera info (if available in the source image).
result: [pending]

### 6. Photo Selection and Metadata
expected: Click different photos in the browser. The metadata panel updates to show each photo's information.
result: [pending]

### 7. Close and Reopen Project
expected: Import photos, save the project, close, and reopen. All photos and their metadata persist correctly.
result: [pending]

## Summary

total: 7
passed: 0
fixed: 4
issues: 0
pending: 3
skipped: 0
