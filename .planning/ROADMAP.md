# Roadmap: HousePhotoMapper

## Overview

HousePhotoMapper delivers a professional desktop application for correlating building photos with 2D architectural plans across 7 phases. The journey begins with foundational architecture and project management (Phase 1), builds the plan viewing engine with PDF tile rendering (Phase 2), adds photo import with EXIF metadata and thumbnails (Phase 3), delivers the complete annotation toolkit with camera geometry and professional shortcuts (Phase 4), implements durable project persistence with auto-save and crash recovery (Phase 5), generates publication-ready PDF reports with camera symbols and figure numbering (Phase 6), and concludes with macOS packaging, notarization, and documentation (Phase 7).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Core Architecture** - Project scaffolding, MVVM skeleton, coordinate system, macOS app bundle (completed 2026-07-13)
- [x] **Phase 2: Plan System** - PDF/PNG/JPG import, multi-page navigation, zoom/pan/rotate, tile pyramid rendering (completed 2026-07-14)
- [ ] **Phase 3: Photo System** - Drag-drop/folder import, EXIF extraction, duplicate detection, lazy-loaded thumbnails
- [ ] **Phase 4: Annotation Tools** - Camera marker, direction arrow, viewing cone, visible polygon, metadata, undo/redo, shortcuts
- [ ] **Phase 5: Project Persistence & Performance** - JSON serialization, auto-save, crash recovery, dark/light mode, <100ms viewport
- [ ] **Phase 6: Report Generation** - Professional PDF reports with photo, plan snippet, camera symbol, cone, metadata, figure numbers
- [ ] **Phase 7: Polish, Packaging & Ship** - macOS notarized DMG, CI/CD, user guide, API docs, v1.0 release

## Phase Details

### Phase 1: Foundation & Core Architecture

**Goal**: User can create, open, save, and save-as projects in a native macOS app with a stable MVVM architecture and coordinate system foundation.
**Depends on**: Nothing (first phase)
**Requirements**: PM-01, PM-02, PM-03, PM-04, CP-01
**Success Criteria** (what must be TRUE):

  1. User can create a new empty project and see an empty plan/photo workspace
  2. User can save the project to a .hpmpj file and reopen it with the same empty state
  3. User can use "Save As" to create a copy of the project at a new path
  4. Application launches as a native macOS app (Apple Silicon + Intel) with proper bundle structure
  5. Coordinate system enum (World Y-up, Screen Y-down, EXIF 8 orientations) is defined and unit-tested

**Plans**: TBD

Plans:

- [x] 01-01: Project scaffolding — uv, pyproject.toml, Ruff, MyPy, pytest-qt, structlog, pre-commit
- [x] 01-02: MVVM skeleton — MainWindow, ProjectVM, ProjectModel, QSettings persistence
- [x] 01-03: Coordinate system — CoordinateSystem enum, central converter with CRSMismatchError, unit tests
- [x] 01-04: PySide6 memory-safe patterns — @Slot() methods, parented QObjects, auto-delete runnables
- [x] 01-05: macOS app bundle — pyproject.toml [tool.pyapp], basic .dmg build, codesign --deep --options runtime

### Phase 2: Plan System

**Goal**: User can import architectural plans (PDF, PNG, JPG), navigate multi-page documents, zoom/pan/rotate smoothly, and view large PDFs via tile pyramid rendering.
**Depends on**: Phase 1
**Requirements**: PI-01, PI-02, PI-03, PI-04, PI-05, PI-06, PI-07
**Success Criteria** (what must be TRUE):

  1. User can import a multi-page PDF plan and see all pages in a page navigator
  2. User can import PNG/JPG plan images and they render correctly
  3. User can zoom in/out (Ctrl+wheel) and pan (middle mouse) with <100ms response
  4. User can rotate plan pages in 90° increments
  5. Large PDFs (>50MB) render via tile pyramid without UI freezing
  6. User can assign floor numbers to plan pages and reorder them

**Plans:** 8 plans (7 complete, 1 gap closure)

Plans:

- [x] 02-01-PLAN.md
- [x] 02-02-PLAN.md
- [x] 02-03-PLAN.md
- [x] 02-04-PLAN.md
- [x] 02-05-PLAN.md
- [x] 02-06-PLAN.md
- [x] 02-07-PLAN.md
- [x] 02-08-PLAN.md

- [x] 02-01: PyMuPDF integration — PDF document model, page rendering to QImage, tile pyramid generator
- [x] 02-02: Plan viewport — QGraphicsScene with NoIndex mode, PlanViewVM, zoom/pan/rotate handlers
- [x] 02-03: Multi-page navigation — page sidebar, floor assignment UI, drag-reorder
- [x] 02-04: Specification-based calibration — known dimension input, second-dimension verification, endpoint snap
- [x] 02-05: PlanModel persistence — serialization to project JSON, coordinate transform storage
- [x] 02-06: Import Plan UI wiring — File menu action, QFileDialog, extension routing to PlanViewModel (gap closure)
- [x] 02-07: Gap closure verification — verify import UI works, update UAT status (gap closure)
- [x] 02-08: PlanView viewport wiring — instantiate PlanView in MainWindow, wire PlanViewModel, add toolbar button (gap closure)

### Phase 3: Photo System

**Goal**: User can import photos via drag-drop or folder scan (recursive), view EXIF metadata, see duplicate detection results, and browse lazy-loaded thumbnails.
**Depends on**: Phase 1 (can parallelize with Phase 2 after Phase 1 complete)
**Requirements**: PH-01, PH-02, PH-03, PH-04, PH-05, PH-06
**Success Criteria** (what must be TRUE):

  1. User can drag and drop photo files onto the app and they appear in the photo browser
  2. User can select a folder and import all photos recursively (subfolders included)
  3. User sees EXIF metadata (timestamp, GPS, camera, lens, orientation) for each photo
  4. Duplicate photos are detected via perceptual hash and flagged for user review
  5. Thumbnails load lazily in background without blocking UI, support virtual scrolling for 1000+ photos
  6. HEIC photos import correctly via pillow-heif

**Plans**: 7 plans

Plans:

- [x] 03-01: Photo models & dependencies — PhotoModel, ExifModel, DuplicateGroup, install imagehash + pillow-heif
- [x] 03-02: Photo import pipeline — PhotoImporter service, drag-drop handler, recursive folder scan
- [x] 03-03: EXIF extraction — ExifExtractor service, GPS rational conversion, orientation handling
- [x] 03-04: Thumbnail system — ThumbnailGenerator with QThreadPool, LRU memory cache, disk cache
- [ ] 03-05: Duplicate detection — DuplicateDetector with dHash, review dialog
- [ ] 03-06: PhotoBrowserVM & UI — PhotoViewModel, PhotoBrowser, PhotoMetadataPanel, MainWindow integration
- [ ] 03-07: Photo persistence & verification — photos.json persistence, full success criteria verification

### Phase 4: Annotation Tools

**Goal**: User can place a camera marker on the plan, set direction and viewing cone, draw a visible-area polygon (4+ points), enter title/description/tags, assign a floor, and edit everything with unlimited undo/redo using professional keyboard shortcuts.
**Depends on**: Phase 2 (PlanModel), Phase 3 (PhotoModel)
**Requirements**: AN-01, AN-02, AN-03, AN-04, AN-05, AN-06, AN-07, AN-08, ED-01, ED-02, ED-03, ED-04, NA-01, NA-02, NA-03, NA-04, NA-05, NA-06, NA-07, NA-08, US-01, US-02
**Success Criteria** (what must be TRUE):

  1. User clicks on plan → camera marker placed; drags from marker → direction arrow appears; adjusts cone angle
  2. User draws visible-area polygon with 4+ points, can snap to plan geometry endpoints
  3. User enters title, description, tags, and selects floor for each annotation
  4. User moves marker, rotates arrow, resizes cone, deletes annotation — all with unlimited undo/redo (Ctrl+Z/Ctrl+Y)
  5. Arrow keys navigate previous/next photo; Space confirms annotation; Delete removes selection; Ctrl+S saves
  6. User completes a full annotation (marker + direction + cone + polygon + metadata) in ≤3 clicks

**Plans**: TBD

Plans:

- [ ] 04-01: Annotation graphics items — CameraMarker, DirectionArrow, ViewingCone, VisibleAreaPolygon (QGraphicsItem)
- [ ] 04-02: AnnotationVM — creation flow, floor selection, metadata form (title, description, tags)
- [ ] 04-03: QUndoStack commands — MoveMarker, RotateArrow, ResizeCone, EditPolygon, DeleteAnnotation, with mergeWith compression
- [ ] 04-04: Keyboard shortcuts — QShortcut with context, configurable keymap, QAction for menu items
- [ ] 04-05: Photo-annotation binding — arrow keys nav, Space to place, selection sync between photo browser and plan

### Phase 5: Project Persistence & Performance

**Goal**: Project saves as JSON with external asset references, auto-saves every 2 minutes, recovers after crash, and delivers dark/light mode with <100ms viewport interaction at standard project sizes.
**Depends on**: Phase 4
**Requirements**: PM-05, RL-01, RL-02, PP-01, PP-02, PP-03, PF-01, PF-02, US-03, US-04
**Success Criteria** (what must be TRUE):

  1. User saves project → .hpmpj JSON file created with plans, photos, annotations, export settings, UI preferences
  2. User opens saved project → all data restores correctly (plan pages, photo thumbnails, annotations, metadata)
  3. Auto-save triggers every 2 minutes silently in background without interrupting workflow
  4. After force-kill and relaunch, user recovers project from auto-save with ≤2 minutes data loss
  5. Dark mode and light mode toggle instantly, persist across sessions
  6. Plan viewport zoom/pan/rotate responds in <100ms at 50 photos / 20 plan pages
  7. Smooth zoom/pan at standard project sizes (no jank, 60fps)

**Plans**: TBD

Plans:

- [ ] 05-01: PersistenceService — atomic JSON writes, .bak files, schema versioning, streaming for large arrays
- [ ] 05-02: Auto-save — QTimer 2-minute interval, background serialization, dirty flag tracking
- [ ] 05-03: Crash recovery — startup scan for .bak/auto-save, recovery dialog, data integrity verification
- [ ] 05-04: Theme system — QPalette-based dark/light, stylesheet variables, OS preference detection, persistence
- [ ] 05-05: Performance baseline — LRU image cache tuning, QGraphicsScene item recycling, benchmark harness

### Phase 6: Report Generation

**Goal**: User generates a professional PDF report with one photo per page, annotated plan snippet, camera symbol with viewing cone, title/description, EXIF metadata, figure numbers, and selectable A4/Letter layout.
**Depends on**: Phase 5
**Requirements**: RG-01, RG-02, RG-03, RG-04, RG-05, RG-06, RG-07, RG-08
**Success Criteria** (what must be TRUE):

  1. User clicks "Generate Report" and gets a PDF with one photo per page
  2. Each page shows the photo, a plan snippet centered on the camera position, camera symbol + viewing cone overlay
  3. Each page includes annotation title, description, and photo metadata (timestamp, camera, lens)
  4. Figure numbers (Figure 1, Figure 2, ...) appear automatically on each page
  5. User selects A4 Portrait, A4 Landscape, or US Letter layout before generation
  6. Report generates in background without freezing UI; 50-photo report completes in <30 seconds
  7. Camera symbol and viewing cone render correctly at plan scale on the plan snippet

**Plans**: TBD

Plans:

- [ ] 06-01: ReportLab template engine — fixed templates first (per research: DSL only if needed in v1.1)
- [ ] 06-02: Plan snippet extraction — render plan region around camera at report DPI, camera symbol + cone overlay
- [ ] 06-03: Per-photo page composition — small tables (ReportLab O(n²) avoidance), pre-calculated heights
- [ ] 06-04: Background generation — ProcessPoolExecutor, progress dialog, cancellation support
- [ ] 06-05: Layout options — A4 Portrait/Landscape, Letter, margins, figure numbering, export settings persistence

### Phase 7: Polish, Packaging & Ship

**Goal**: Deliver a notarized macOS .dmg installer, CI/CD pipeline, user guide, and API documentation ready for v1.0 release.
**Depends on**: Phase 6
**Requirements**: (All v1 requirements covered in Phases 1-6; this phase delivers the shippable product)
**Success Criteria** (what must be TRUE):

  1. User downloads .dmg, installs app, and it launches without Gatekeeper warnings (notarized, hardened runtime)
  2. CI/CD runs on every push: lint, type-check, unit tests, UI tests, build .dmg, notarization
  3. User guide covers: project workflow, plan import, photo import, annotation, report generation, keyboard shortcuts
  4. API documentation generated from docstrings covers all public ViewModels, Models, and Services
  5. App starts in <3 seconds on M1/M2 Mac; bundle size <150MB (excluded unused PySide6 modules)

**Plans**: TBD

Plans:

- [ ] 07-01: pyappdist/ux configuration — DMG build, codesign --deep --force --options runtime, entitlements.plist
- [ ] 07-02: Notarization CI — GitHub Actions workflow, xcrun notarytool submit, staple, artifact upload
- [ ] 07-03: Bundle optimization — --exclude-module for unused PySide6, pyi-makespec profiling, size audit
- [ ] 07-04: User guide — Markdown → HTML/PDF, screenshots, workflow tutorials, shortcut cheat sheet
- [ ] 07-05: API docs — pdoc/mkdocstrings, module reference, architecture decision log

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Core Architecture | 5/5 | Complete    | 2026-07-13 |
| 2. Plan System | 7/7 | In progress   | - |
| 3. Photo System | 0/TBD | Not started | - |
| 4. Annotation Tools | 0/TBD | Not started | - |
| 5. Project Persistence & Performance | 0/TBD | Not started | - |
| 6. Report Generation | 0/TBD | Not started | - |
| 7. Polish, Packaging & Ship | 0/TBD | Not started | - |

## Parallelization & Critical Path

**Parallelization Opportunities** (config.parallelization=true):

- Phase 2 (Plan System) and Phase 3 (Photo System) can run in parallel after Phase 1 — they share only ProjectModel/PersistenceService
- Phase 7 (Polish/Packaging) documentation tasks (07-04, 07-05) can overlap with 07-01/07-02/07-03

**Critical Path:**
Phase 1 → Phase 2 → Phase 4 → Phase 5 → Phase 6 → Phase 7

(Phase 3 can parallelize with Phase 2. Phase 4 depends on both PlanModel from Phase 2 and PhotoModel from Phase 3. Phase 5 depends on Phase 4. Phase 6 depends on Phase 5. Phase 7 depends on Phase 6.)

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PM-01 | Phase 1 | Pending |
| PM-02 | Phase 1 | Pending |
| PM-03 | Phase 1 | Pending |
| PM-04 | Phase 1 | Pending |
| PM-05 | Phase 5 | Pending |
| PI-01 | Phase 2 | Pending |
| PI-02 | Phase 2 | Pending |
| PI-03 | Phase 2 | Pending |
| PI-04 | Phase 2 | Pending |
| PI-05 | Phase 2 | Pending |
| PI-06 | Phase 2 | Pending |
| PI-07 | Phase 2 | Pending |
| PH-01 | Phase 3 | Pending |
| PH-02 | Phase 3 | Pending |
| PH-03 | Phase 3 | Pending |
| PH-04 | Phase 3 | Pending |
| PH-05 | Phase 3 | Pending |
| PH-06 | Phase 3 | Pending |
| AN-01 | Phase 4 | Pending |
| AN-02 | Phase 4 | Pending |
| AN-03 | Phase 4 | Pending |
| AN-04 | Phase 4 | Pending |
| AN-05 | Phase 4 | Pending |
| AN-06 | Phase 4 | Pending |
| AN-07 | Phase 4 | Pending |
| AN-08 | Phase 4 | Pending |
| ED-01 | Phase 4 | Pending |
| ED-02 | Phase 4 | Pending |
| ED-03 | Phase 4 | Pending |
| ED-04 | Phase 4 | Pending |
| NA-01 | Phase 4 | Pending |
| NA-02 | Phase 4 | Pending |
| NA-03 | Phase 4 | Pending |
| NA-04 | Phase 4 | Pending |
| NA-05 | Phase 4 | Pending |
| NA-06 | Phase 4 | Pending |
| NA-07 | Phase 4 | Pending |
| NA-08 | Phase 4 | Pending |
| RG-01 | Phase 6 | Pending |
| RG-02 | Phase 6 | Pending |
| RG-03 | Phase 6 | Pending |
| RG-04 | Phase 6 | Pending |
| RG-05 | Phase 6 | Pending |
| RG-06 | Phase 6 | Pending |
| RG-07 | Phase 6 | Pending |
| RG-08 | Phase 6 | Pending |
| PP-01 | Phase 5 | Pending |
| PP-02 | Phase 5 | Pending |
| PP-03 | Phase 5 | Pending |
| PF-01 | Phase 5 | Pending |
| PF-02 | Phase 5 | Pending |
| RL-01 | Phase 5 | Pending |
| RL-02 | Phase 5 | Pending |
| US-01 | Phase 4 | Pending |
| US-02 | Phase 4 | Pending |
| US-03 | Phase 5 | Pending |
| US-04 | Phase 5 | Pending |
| CP-01 | Phase 1 | Pending |

**Coverage:**

- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓
