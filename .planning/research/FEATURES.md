# Feature Landscape: Desktop Architectural Photo Documentation

**Domain:** Desktop architectural documentation — correlating photographs with 2D floor plans for professional PDF reports
**Researched:** 2025-07-13
**Mode:** Ecosystem survey of desktop AEC photo documentation, plan markup, and report generation tools

---

## Executive Summary

The desktop architectural photo documentation market splits into three distinct categories:

| Category | Examples | Core Focus | Platform |
|----------|----------|------------|----------|
| **Desktop PDF Markup** | Bluebeam Revu, PDF Studio, PDF-XChange | PDF annotation, takeoffs, markup | Windows (Bluebeam), Cross-platform (PDF Studio) |
| **Cloud/Field-First Platforms** | PlanGrid/Autodesk Build, Fieldwire, Procore, OpenSpace, Filio | Field capture, issue tracking, project mgmt | Mobile-first, cloud sync |
| **Specialized Photo-on-Plan** | pin360, kontekst lens, PhotoReport, EarthCam, DroneDeploy Ground | Pin photos to PDF plans, generate reports | Web/mobile, some desktop viewers |

**HousePhotoMapper's whitespace:** No competitor occupies the **desktop-first, professional architectural documentation** niche that combines:
- PDF plan import (not scanning/capture)
- Camera position + direction + viewing cone + visible area polygon annotation
- Professional PDF reports with camera symbols, viewing cones, figure numbers, custom layouts
- 1000+ photo / 100+ plan performance on desktop
- Perpetual license, macOS-first native app
- AI-ready architecture for future auto-positioning

---

## Table Stakes

*Features users expect. Missing = product feels incomplete or unprofessional.*

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Project management** (create, open, save, save-as, auto-save) | Baseline for any document-based desktop app | Low | JSON format, external assets, auto-save 2min |
| **Multi-page PDF plan import** with zoom/pan/rotate | Users receive multi-sheet PDF plan sets | Medium | PyMuPDF (fitz); tile rendering for large PDFs |
| **Photo import** (JPG/PNG/HEIC, drag-drop, folder import, recursive, EXIF extraction, duplicate detection) | Core workflow starts with photo ingestion | Medium | Pillow + ExifRead; perceptual hashing for dupes |
| **Photo browser** (thumbnails, metadata, sort by date/name/status/room, filter annotated/unannotated, interior/exterior) | Managing 1000+ photos requires organization | Medium | Lazy-loaded thumbnails, SQLite index |
| **Camera position marker** (point on plan) | Minimum viable annotation | Low | QGraphicsScene item with snap |
| **Camera direction arrow** (rotate from marker) | Shows where camera pointed | Low | Rotatable arrow item |
| **Viewing cone** (adjustable FOV angle) | Shows field of view | Medium | Adjustable angle arc + rays |
| **Visible area polygon** (4+ point polygon for occlusions) | Real-world visibility isn't a perfect cone | Medium | Polygon editor with snap |
| **Annotation metadata** (title, description, tags, floor selection) | Professional reports need structured data | Low | Per-annotation property panel |
| **Edit operations** (move, rotate, resize, delete, copy/paste, unlimited undo/redo) | Professional editing expectations | Medium | Command pattern + QUndoStack |
| **Keyboard shortcuts** (arrows, space+pan, Ctrl+S, Ctrl+Z/Y, Del, zoom/pan) | Power users expect CAD-like shortcuts | Low | QShortcut / event filter |
| **Professional PDF report generation** (photo + plan + camera symbol + cone + title + description + metadata + figure numbers + A4/Letter/custom) | Primary deliverable | High | ReportLab; template system |
| **Project persistence** (JSON + external assets, versionable) | Collaboration, backup, version control | Low | Structured JSON schema |
| **Performance**: 1000+ photos, 100+ plan pages, smooth zoom/pan | Stated success metric | High | Tile rendering, LRU cache, background workers |
| **Reliability**: auto-save 2min, crash recovery, project backup | Professional reliability expectation | Medium | Atomic writes, .bak files, recovery dialog |
| **Usability**: ≤3 clicks per annotation, dark/light mode, professional shortcuts | "Minimize time to document" core value | Medium | UX testing target |
| **macOS native app** (v1) | Strategic decision: macOS-first | Medium | PySide6 + PyInstaller .app bundle |

---

## Differentiators

*Features that create competitive advantage. Not expected, but highly valued by target users.*

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Camera position + direction + viewing cone + visible area polygon** (all four) | Most tools only do photo pinning; full camera geometry enables precise documentation | High | Core differentiator vs. pin360, PhotoReport, kontekst |
| **Professional PDF reports with camera symbols, viewing cones, figure numbers, custom layouts** | Output looks like architectural documentation, not a photo collage | High | ReportLab templates; figure numbering per floor/plan |
| **Desktop-first native app (PySide6/Qt)** | No browser latency, works offline, native menus/shortcuts, large dataset performance | Medium | vs. pin360 (web), PhotoReport (iOS), kontekst (mobile) |
| **Perpetual license model** | No subscription fatigue; aligns with desktop tool expectations | Low (biz) | vs. Bluebeam ($49/mo), PlanGrid ($39+/mo), Fieldwire ($39+/mo) |
| **macOS-first, then Windows/Linux** | Underserved platform; architects use Macs | Medium | PySide6 cross-platform; codesign/notarization |
| **1000+ photos / 100+ plans at 60fps** | Handles real projects without lag | High | Tile pyramid rendering, background thumbnail gen, memory-mapped assets |
| **AI-ready architecture** (room recognition, auto-positioning hooks) | Future-proofs for v1.1 AI features without rewrite | Medium | Plugin points in annotation pipeline; ONNX runtime ready |
| **JSON project format + external assets** | Git-friendly, diffable, no vendor lock-in | Low | vs. proprietary DBs (Bluebeam, PlanGrid) |
| **Per-annotation floor/plan selection** | Multi-floor projects need explicit floor assignment | Low | Dropdown in annotation panel |
| **Customizable report layouts** (A4, Letter, custom margins, branding, cover page) | Professional deliverables match firm standards | Medium | ReportLab template DSL |
| **Visible area polygon with occlusion handling** | Real walls block view; cone alone is inaccurate | Medium | Polygon editor with snap to plan geometry |
| **EXIF-driven auto-sort** (date, GPS, camera) | Reduces manual organization time | Low | Pillow + ExifRead; GPS clustering for exterior |
| **Duplicate detection** (perceptual hash) | Prevents clutter from re-imports | Medium | imagehash library |
| **Unlimited undo/redo with command compression** | Professional editing confidence | Medium | QUndoStack + macro commands |

---

## Anti-Features

*Features to explicitly NOT build. Stated in requirements as Out of Scope.*

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time chat / collaboration** | High complexity, not core to documentation value | Export PDF/share project file |
| **Video capture / playback** | Storage/bandwidth costs, defer to v2+ | Link to external video files |
| **OAuth / social login** | Email/password sufficient for v1 desktop app | Local auth or none (file-based) |
| **Mobile app (iOS/Android)** | Web-first, mobile later; desktop is primary workspace | Responsive web viewer for report consumers (v2) |
| **3D model support (IFC, Revit, SketchUp)** | Future v2.0; scope creep for v1 | PDF plan import covers 90% of workflows |
| **IFC/Revit/AutoCAD direct integration** | Future v2.0; licensing complexity | PDF export from CAD is standard workflow |
| **Cloud synchronization** | Future v2.0; infrastructure cost/complexity | Local files + user's preferred sync (iCloud, Dropbox) |
| **Multi-user concurrent editing** | Future v2.0; conflict resolution complexity | File-based sharing; one editor at a time |
| **360° photos / drone / thermal / point clouds** | Future extensions; different capture workflow | Standard photos cover core use case |
| **Takeoff / measurement / estimating** | Bluebeam owns this; not core value | Partner/integrate later if needed |
| **Project management / scheduling / RFIs / submittals** | Procore/Fieldwire territory; bloats app | Focus on documentation only |
| **BIM viewer / model coordination** | Autodesk/Trimble territory; different product | 2D plan + photo is the workflow |
| **Field capture / on-site photo taking** | Desktop app; users import from camera/phone | Optimize import workflow instead |
| **Subscription licensing** | Desktop users expect perpetual; competitive diff | One-time purchase + paid major upgrades |

---

## Feature Dependencies

```
Project Management (FR-1)
    └── Plan Import (FR-2)
            └── Photo Import (FR-3)
                    └── Photo Browser (FR-4)
                            └── Annotation (FR-5) ← Camera pos, dir, cone, polygon, metadata
                                    ├── Editing (FR-6) ← Move, rotate, resize, delete, copy/paste, undo/redo
                                    ├── Navigation (FR-7) ← Shortcuts, zoom/pan
                                    └── Report Generation (FR-8) ← Requires annotations + plan + photos + metadata
                                            └── Project Persistence (FR-9) ← JSON save/load
```

**Critical Path:** FR-1 → FR-2 → FR-3 → FR-4 → FR-5 → FR-6/FR-7 → FR-8 → FR-9

**Performance Dependencies (NFR-Perf):**
- Tile rendering pyramid → depends on FR-2 (plan rendering)
- Background thumbnail generation → depends on FR-3 (photo import)
- LRU memory/disk cache → depends on FR-2, FR-3
- Lazy loading in photo browser → depends on FR-4

**Reliability Dependencies (NFR-Reliability):**
- Auto-save → depends on FR-9 (persistence)
- Crash recovery → depends on FR-9 (atomic writes, .bak)
- Project backup → depends on FR-9

---

## MVP Recommendation

**Prioritize (Phase 0-6):**
1. **Project management** (FR-1) — Foundation
2. **Plan import** (FR-2) — Core input
3. **Photo import** (FR-3) — Core input
4. **Photo browser** (FR-4) — Organization
5. **Annotation: camera position + direction + viewing cone** (FR-5 core) — Core differentiator
6. **Editing: move/rotate/delete + undo/redo** (FR-6 core) — Usability
7. **Navigation shortcuts** (FR-7) — Power user expectation
8. **Report generation: basic PDF with photo + plan + camera symbol + cone + metadata** (FR-8 core) — Primary deliverable
9. **Project persistence: JSON + assets** (FR-9) — Data ownership

**Defer to Phase 7-9:**
- Visible area polygon (FR-5 advanced) — Nice-to-have for v1
- Copy/paste annotations (FR-6 advanced)
- Custom report layouts / branding (FR-8 advanced)
- Duplicate detection (FR-3 advanced)
- EXIF auto-sort (FR-4 advanced)
- Floor selection per annotation (FR-5 metadata)
- Advanced filters (FR-4 advanced)

**Defer to v1.1+ (Post-MVP):**
- AI-assisted room recognition / auto-positioning
- 360° photo support
- Web report viewer (shareable links)
- Windows/Linux builds
- Plugin/extension API

---

## Competitive Feature Matrix

| Feature | HousePhotoMapper | Bluebeam Revu | pin360 | PhotoReport | kontekst lens | Fieldwire/PlanGrid |
|---------|------------------|---------------|--------|-------------|---------------|-------------------|
| **Platform** | Desktop (macOS/Win/Linux) | Desktop (Win) + Web | Web | iOS/iPadOS | Mobile + Web | Mobile + Web |
| **License** | Perpetual | Subscription ($49/mo) | Freemium | Freemium | Subscription | Subscription ($39+/mo) |
| **PDF Plan Import** | ✅ Multi-page | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Photo Import** | ✅ Batch, EXIF, dupes | ⚠️ Manual | ✅ | ✅ | ✅ | ✅ |
| **Photo Browser** | ✅ Thumbnails, filters | ❌ | ✅ Basic | ✅ | ✅ | ✅ |
| **Camera Position** | ✅ | ✅ Markup | ✅ Pin | ✅ Pin | ✅ Pin | ✅ Pin |
| **Camera Direction** | ✅ Arrow | ✅ Line tool | ❌ | ❌ | ❌ | ❌ |
| **Viewing Cone** | ✅ Adjustable FOV | ✅ Custom tool | ❌ | ❌ | ❌ | ❌ |
| **Visible Area Polygon** | ✅ | ⚠️ Polygon tool | ❌ | ❌ | ❌ | ❌ |
| **Annotation Metadata** | ✅ Title, desc, tags, floor | ✅ Custom props | ⚠️ Notes | ⚠️ Notes | ✅ Tags | ✅ Rich |
| **Undo/Redo** | ✅ Unlimited | ✅ | ❌ | ⚠️ Limited | ❌ | ✅ |
| **Keyboard Shortcuts** | ✅ CAD-like | ✅ Extensive | ❌ | ❌ | ❌ | ⚠️ Basic |
| **PDF Report** | ✅ Pro: symbols, cones, fig# | ✅ Markup summary | ✅ Basic | ✅ Basic | ✅ Basic | ✅ Issue reports |
| **Custom Report Layouts** | ✅ Template DSL | ⚠️ Templates | ❌ | ❌ | ❌ | ⚠️ Templates |
| **Performance (1K photos)** | ✅ Target | ⚠️ Lags | N/A (cloud) | N/A (mobile) | N/A (mobile) | N/A (cloud) |
| **Offline** | ✅ Native | ✅ | ❌ | ✅ | ✅ Offline sync | ✅ Offline sync |
| **AI Hooks** | ✅ Architecture ready | ❌ | ❌ | ❌ | ❌ | ✅ Some AI |

---

## Sources

- Bluebeam Revu vs Fieldwire/PlanGrid/Procore comparisons: SelectHub, Softabase, RFP.wiki, Under the Hard Hat (2025-2026)
- pin360.io — Pin 360° Site Photos to PDF Floor Plans
- photoreport.app — Photo Reports App (iOS/iPadOS)
- kontekst.app — Construction Photo Documentation
- filio.io — AI-Powered Visual Documentation
- EarthCam Control Center 9 — Photography Documentation
- DroneDeploy Ground — 360° Site Documentation
- OpenSpace Capture — 360° Reality Capture
- docu-tools.com — 360° Photos Integration
- Spacewise — AI Floor Plans + Photo Pinning (Snapshots Report)
- IPVM Discussion: "Good Software/App For PDF Floor Plan Markup?" — Practitioner recommendations (Bluebeam, PDF Studio, Visio, JVSG)
- Metaroom / Amrax — 3D Scanning + 2D Plan Export
- 4lines.ai / SceneVista.ai — Browser-based floor plan + camera placement (AI rendering focus)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Table Stakes | HIGH | Directly from validated requirements (FR-1 through FR-9, NFRs) + competitive parity |
| Differentiators | HIGH | Clear whitespace identified; no competitor combines all four annotation geometries + desktop + pro reports |
| Anti-Features | HIGH | Explicitly documented in PROJECT.md Out of Scope with rationale |
| Feature Dependencies | MEDIUM | Logical dependency chain; some parallelization possible (e.g., FR-7 shortcuts can be built anytime) |
| MVP Prioritization | MEDIUM | Based on core value "minimize time to document"; defer visible-area-polygon validated as advanced |
| Competitive Matrix | MEDIUM | Based on public marketing pages + review summaries; some features inferred from screenshots |

---

## Gaps to Address in Phase-Specific Research

- **Phase 2 (Plan Import):** PDF rendering performance at 100+ pages — need tile pyramid benchmarks
- **Phase 3 (Photo Import):** HEIC support on macOS (Pillow + pillow-heif) — verify licensing
- **Phase 5 (Annotation):** Visible area polygon UX — research polygon editing patterns in CAD apps
- **Phase 8 (Reports):** ReportLab template DSL design — evaluate Jinja2 vs custom vs WeasyPrint alternative
- **Phase 11 (Performance):** Memory mapping strategy for 1000+ photos — test mmap vs SQLite blob vs filesystem
