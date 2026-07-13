# HousePhotoMapper

## What This Is

HousePhotoMapper is a desktop application that enables users to correlate photographs of a building (interior and exterior) with 2D architectural plans. Users import architectural plans (PDF) and photo collections, place each photo on the appropriate floor plan with camera position and viewing direction, and automatically generate professional documentation reports in PDF format. Target users include homeowners, architects, surveyors, building inspectors, insurance companies, property managers, and construction companies.

## Core Value

Minimize the time required to document a building while producing professional, editable reports without manual desktop publishing.

## Business Context

- **Customer**: Homeowners, architects, surveyors, building inspectors, insurance companies, property managers, construction companies
- **Revenue model**: Direct software sales (desktop application)
- **Success metric**: Users can annotate a photo in <10 seconds after import; handle 1000+ photos and 100+ plan pages
- **Strategy notes**: Future AI-assisted workflows (room recognition, auto-positioning) planned without major architectural changes

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **FR-1**: Project management — create, open, save, save-as, auto-save projects
- [ ] **FR-2**: Plan import — PDF, PNG, JPG, TIFF support with multi-page, zoom, pan, rotation
- [ ] **FR-3**: Photo import — JPG, JPEG, PNG, HEIC with drag-drop, folder import, recursive scan, EXIF extraction, duplicate detection
- [ ] **FR-4**: Photo browser — thumbnails, metadata display, sorting (date, name, status, room), filtering (annotated/unannotated, exterior/interior)
- [ ] **FR-5**: Annotation — camera position, direction, viewing cone, visible area polygon, title, description, tags, floor selection
- [ ] **FR-6**: Editing — move marker, rotate arrow, resize cone, delete, copy/paste, unlimited undo/redo
- [ ] **FR-7**: Navigation — keyboard shortcuts (arrows, space, Ctrl+S, Ctrl+Z/Y, delete, zoom/pan)
- [ ] **FR-8**: Report generation — professional PDF with photo, plan, camera symbol, viewing cone, title, description, metadata, figure numbers, A4/Letter/custom layouts
- [ ] **FR-9**: Project persistence — JSON-based format storing plans, photos, metadata, annotations, export settings, UI preferences
- [ ] **NFR-Perf**: 1000+ photos, 100+ plan pages, smooth zoom/pan, fast loading
- [ ] **NFR-Reliability**: Auto-save every 2 min, crash recovery, project backup
- [ ] **NFR-Usability**: Max 3 clicks per annotation, professional shortcuts, dark/light mode
- [ ] **NFR-Compat**: macOS (v1), Windows 11/10 (future), Linux (future)

### Out of Scope

- Real-time chat — High complexity, not core to documentation value
- Video posts — Storage/bandwidth costs, defer to v2+
- OAuth login — Email/password sufficient for v1
- Mobile app — Web-first, mobile later
- 3D model support — Future v2.0
- IFC/Revit/AutoCAD integration — Future v2.0
- Cloud synchronization — Future v2.0
- Multi-user editing — Future v2.0
- 360° photos / video / drone / thermal / point clouds — Future extensions

## Context

- Existing PRD.md and PLAN.md define detailed requirements and 12-phase implementation plan
- Technology stack: Python 3.12+, PySide6 (Qt), PyMuPDF, Pillow, OpenCV (optional), ReportLab, JSON/SQLite, pytest, Black/Ruff/MyPy, PyInstaller, GitHub Actions
- Architecture: MVVM with dependency injection, Qt signal/slot event bus, central project model, undo/redo framework
- Graphics: QGraphicsScene with custom items (CameraMarker, Arrow, ViewingCone, VisibleArea, Label) supporting selection, dragging, rotation, serialization, undo/redo
- Performance targets: <100ms viewport interaction, background thumbnail/PDF rendering, tile rendering, lazy loading, memory/disk cache

## Constraints

- **Tech stack**: Python 3.12+, PySide6 — Cross-platform desktop framework choice
- **Timeline**: 12 phases defined; Phase 0 (setup) to Phase 12 (documentation)
- **Compatibility**: macOS first, Windows/Linux future — Limits immediate platform testing
- **Performance**: 1000+ photos, 100+ plan pages — Requires optimized rendering and caching
- **Dependencies**: PyMuPDF for PDF, ReportLab for report generation — Licensing/compatibility considerations

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + PySide6 | Cross-platform, mature ecosystem, good PDF/image libs | — Pending |
| JSON project format (assets external) | Simplicity, version control friendly, avoid large binaries | — Pending |
| MVVM architecture | Separation of concerns, testability, Qt-native | — Pending |
| QGraphicsScene for annotations | Vector-based, performant, built-in selection/transform | — Pending |
| ReportLab for PDF generation | Programmatic control, professional output, Python-native | — Pending |
| 12-phase sequential plan | Clear milestones, manageable scope per phase | — Pending |
| macOS-first, Windows/Linux later | Reduce initial platform complexity | — Pending |
| AI features deferred to v1.1+ | Focus on core workflow first, architecture ready for AI | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Business Context check — customer, revenue model, success metric still accurate?
4. Audit Out of Scope — reasons still valid?
5. Update Context with current state (users, feedback, metrics)

---
*Last updated: 2025-07-13 after initialization*