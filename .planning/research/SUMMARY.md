# Project Research Summary

**Project:** HousePhotoMapper
**Synthesized:** 2025-07-13
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Key Findings

### Stack (from STACK.md)

**Core Framework:** Python 3.12+, PySide6 6.11+ (Qt 6.11 LTS) — LGPL allows closed-source distribution without fees. PyQt6 rejected due to GPL commercial license costs.

**PDF Processing:** PyMuPDF 1.24+ for rendering/extraction (10x faster than alternatives), ReportLab 4.3+ for professional report generation. **Critical:** PyMuPDF is AGPL-3.0 — requires commercial license evaluation for closed-source distribution.

**Image Processing:** Pillow 11.1+ + pillow-heif 1.4+ for HEIC support. OpenCV 4.11+ optional for future AI features.

**Packaging:** PyInstaller 6.13+ for dev builds; pyappdist/ux for production native installers (MSI, DMG with notarization, AppImage).

**Dependency Management:** uv 0.5+ (10-20x faster than pip/Poetry, replaces pyenv+pip+venv+pip-tools).

**Code Quality:** Ruff (consolidates Black+Flake8+isort+pydocstyle+pyupgrade), MyPy for type checking.

**Testing:** pytest + pytest-qt for UI tests.

**Undo/Redo:** QUndoStack + QUndoCommand (Qt native).

**Logging:** structlog for structured logging with OpenTelemetry integration.

**Auto-Update:** tufup (TUF-based secure updates).

### Table Stakes (from FEATURES.md)

15 features from validated requirements (FR-1 through FR-9 + NFRs) map directly to competitive parity requirements. Categories: Project Management, Plan Import, Photo Import, Photo Browser, Camera Position + Direction + Cone + Visible Area Polygon, Annotation Metadata, Edit Operations, Keyboard Shortcuts, Professional PDF Reports, Project Persistence, Performance (1000+ photos, 100+ plans), Reliability (auto-save, crash recovery), Usability (≤3 clicks/annotation), macOS native app.

### Differentiators (from FEATURES.md)

- **Full camera geometry** (position + direction + cone + visible polygon) — competitors only do photo pinning
- **Professional PDF reports** with camera symbols, viewing cones, figure numbers, custom layouts
- **Desktop-first native app** — no browser latency, offline, native shortcuts
- **Perpetual license** — vs. Bluebeam ($49/mo), PlanGrid ($39+/mo)
- **macOS-first** — underserved platform for architects
- **1000+ photos / 100+ plans at 60fps** — tile pyramid rendering, background workers
- **AI-ready architecture** — plugin points for v1.1 room recognition/auto-positioning
- **JSON + external assets** — Git-friendly, diffable, no vendor lock-in

### Anti-Features (from FEATURES.md)

Explicitly excluded: real-time chat, video, OAuth, mobile apps, 3D/IFC/Revit, cloud sync, multi-user editing, 360°/drone/thermal, takeoff/measurement, project management, BIM viewer, field capture, subscription licensing.

### Architecture (from ARCHITECTURE.md)

**Pattern:** MVVM with Qt Signal/Slot Event Bus.

**Key Components:**
- MainWindow (View) — top-level window, docking
- ProjectVM — project lifecycle, undo/redo coordination
- PlanViewVM — plan viewport, annotation tools, PDF rendering
- PhotoBrowserVM — photo library, filtering, metadata
- AnnotationVM — marker/arrow/cone/polygon creation/editing
- ReportVM — report templates, PDF generation
- ProjectModel — central data (plans, photos, annotations, settings)
- PlanModel — multi-page PDF, page rendering, coordinate transforms
- PhotoModel — metadata, thumbnails, duplicate detection
- PersistenceService — JSON serialization, auto-save, crash recovery
- PDF Engine (PyMuPDF) — rendering, extraction
- Image Cache — thumbnails, LRU memory/disk cache
- Report Generator (ReportLab) — professional PDF composition

**Build Order:** Core infrastructure → Plan system → Photo system → Annotations → Persistence → Reports → Polish → Packaging. Phase 3 (photos) can parallel Phase 2 (plans) after Phase 1.

### Pitfalls (from PITFALLS.md)

| # | Pitfall | Severity | Prevention | Phase |
|---|---------|----------|------------|-------|
| 1 | QGraphicsScene BSP tree degradation with overlapping items | Critical | `NoIndex` mode, item recycling, clustering at low zoom | 3, 5 |
| 2 | ReportLab O(n²) slowdown on multi-page reports | Critical | Small tables per photo, pre-calc heights, background process pool | 8 |
| 3 | PDF plan scale calibration drift | Critical | Specification-based calibration, verify 2nd dimension, snap to endpoints | 2, 5 |
| 4 | Photo memory explosion (1000+ high-res) | Critical | Tile-based lazy loading, `setScaledSize()`, background EXIF pool, virtual scrolling | 4 |
| 5 | PySide6 memory leaks (lambdas, autoDelete=False) | Moderate | `@Slot()` methods only, parented QObjects, auto-delete runnables | 0, 1 |
| 6 | Coordinate system mismatch (WORLD Y-up vs SCREEN Y-down vs EXIF 8 orientations) | Moderate | Explicit `CoordinateSystem` enum + central converter with `CRSMismatchError` | 1 |
| 7 | EXIF orientation handling (8 orientations) | Moderate | Apply orientation transform on load, cache corrected thumbnails | 4 |
| 8 | JSON project file size/corruption | Moderate | Atomic writes, .bak files, schema versioning, streaming for large arrays | 6 |
| 9 | PyInstaller bundle size/startup | Moderate | Exclude unused PySide6 modules, `--exclude-module`, profile with `pyi-makespec` | 11 |
| 10 | macOS codesign/notarization failures | Moderate | Test notarization in CI, `codesign --deep --force --options runtime`, entitlements | 11 |
| 11 | Undo stack growth unbounded | Minor | Command compression (`mergeWith`), configurable stack depth | 5 |
| 12 | Annotation serialization complexity | Minor | Separate geometry + metadata, versioned schema, migration path | 5 |
| 13 | Report template DSL complexity | Minor | Start with fixed templates, DSL only if needed in v1.1 | 8 |
| 14 | Multi-monitor DPI scaling | Minor | `QGuiApplication.setHighDpiScaleFactorRoundingPolicy`, test on Retina + external | 1 |
| 15 | Keyboard shortcut conflicts | Minor | `QShortcut` with context, configurable keymap, `QAction` for menu items | 5 |
| 16 | Photo duplicate false positives/negatives | Minor | Perceptual hash (pHash) + size check, user review for edge cases | 4 |
| 17 | Plan page order vs. user floor order | Minor | Explicit floor assignment per page, drag-reorder in project explorer | 2 |

---

## Implications for Roadmap

### Phase Structure (aligned with PLAN.md + research)

| Phase | Focus | Key Research Dependencies |
|-------|-------|---------------------------|
| 0 | Setup | uv, pyproject.toml, Ruff, MyPy, pytest-qt, structlog, pre-commit |
| 1 | Core Architecture | MVVM skeleton, QSettings, coordinate system enum, PySide6 memory-safe patterns |
| 2 | PDF Engine | PyMuPDF integration, **spec-based calibration**, tile pyramid rendering, AGPL license eval |
| 3 | Plan Import & Annotation Layer | QGraphicsScene `NoIndex`, item recycling, clustering, scale calibration UI |
| 4 | Photo Import & Browser | Pillow + pillow-heif + piexif, `setScaledSize()`, background EXIF pool, virtual scrolling |
| 5 | Annotation Tools | QUndoStack commands, command compression, visible area polygon editor, snap to plan geometry |
| 6 | Project Persistence | Atomic JSON writes, .bak files, schema versioning, auto-save 2min |
| 7 | Report Generation | ReportLab small tables per photo, pre-calc heights, background `ProcessPoolExecutor`, figure numbering |
| 8 | User Interface | Dock widgets, dark/light mode, professional shortcuts, report template selection |
| 9 | Performance Optimization | Benchmarks on target hardware (M1/M2, Windows laptop), LRU cache tuning |
| 10 | Testing | pytest-qt integration, golden PDF comparison, large project regression tests |
| 11 | Packaging | pyappdist/ux, notarized macOS .dmg, signed Windows .msi, Linux .run |
| 12 | Documentation | Developer guide, user guide, API docs |

### Parallelization Opportunities

- **Phase 2 (Plans)** and **Phase 3 (Photos)** can run in parallel after Phase 1 — they share only ProjectModel/PersistenceService
- **Phase 8 (UI Polish)** and **Phase 9 (Performance)** overlap — profile while polishing
- **Phase 10 (Testing)** continuous — run in CI on every merge

### Critical Path

Phase 1 → Phase 2 → Phase 4 → Phase 5 → Phase 6 → Phase 7

(Annotations in Phase 5 depend on PlanModel from Phase 2 and PhotoModel from Phase 3/4)

---

## Sources

- STACK.md — Technology recommendations with versions, rationale, alternatives
- FEATURES.md — Feature landscape: table stakes, differentiators, anti-features, dependencies
- ARCHITECTURE.md — Component boundaries, data flows, build order, patterns
- PITFALLS.md — 17 pitfalls (4 critical, 6 moderate, 7 minor) with prevention strategies and phase mapping
