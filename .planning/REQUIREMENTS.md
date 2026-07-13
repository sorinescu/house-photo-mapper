# Requirements: HousePhotoMapper

**Defined:** 2025-07-13
**Core Value:** Minimize the time required to document a building while producing professional, editable reports without manual desktop publishing.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Project Management

- [x] **PM-01**: User can create a new project
- [x] **PM-02**: User can open an existing project
- [x] **PM-03**: User can save a project
- [x] **PM-04**: User can save project as (Save As)
- [ ] **PM-05**: User project auto-saves every 2 minutes

### Plan Import

- [ ] **PI-01**: User can import PDF architectural plans
- [ ] **PI-02**: User can import PNG/JPG plan images
- [ ] **PI-03**: User can navigate multi-page plans
- [ ] **PI-04**: User can zoom in/out on plan
- [ ] **PI-05**: User can pan across plan
- [ ] **PI-06**: User can rotate plan pages
- [ ] **PI-07**: Plan renders with tile pyramid for large PDFs

### Photo Import

- [ ] **PH-01**: User can import photos via drag & drop
- [ ] **PH-02**: User can import photos from folder
- [ ] **PH-03**: User can import photos from folder recursively
- [ ] **PH-04**: System extracts EXIF metadata (timestamp, GPS, camera, lens, orientation)
- [ ] **PH-05**: System detects duplicate photos (perceptual hash)
- [ ] **PH-06**: System generates thumbnails (lazy-loaded, background)

### Annotation

- [ ] **AN-01**: User can place camera position marker on plan
- [ ] **AN-02**: User can set camera direction arrow from marker
- [ ] **AN-03**: User can adjust viewing cone angle
- [ ] **AN-04**: User can draw visible area polygon (4+ points)
- [ ] **AN-05**: User can enter title for annotation
- [ ] **AN-06**: User can enter description for annotation
- [ ] **AN-07**: User can add tags to annotation
- [ ] **AN-08**: User can select floor for annotation

### Editing

- [ ] **ED-01**: User can move camera marker
- [ ] **ED-02**: User can rotate direction arrow
- [ ] **ED-03**: User can delete annotation
- [ ] **ED-04**: Unlimited undo/redo for all edits

### Navigation

- [ ] **NA-01**: Arrow keys navigate previous/next photo
- [ ] **NA-02**: Space key confirms/places annotation
- [ ] **NA-03**: Ctrl+S saves project
- [ ] **NA-04**: Ctrl+Z undoes last action
- [ ] **NA-05**: Ctrl+Y redoes last undone action
- [ ] **NA-06**: Delete key removes selected annotation
- [ ] **NA-07**: Ctrl+Mouse wheel zooms plan
- [ ] **NA-08**: Middle mouse button pans plan

### Report Generation

- [ ] **RG-01**: User can generate professional PDF report
- [ ] **RG-02**: Report includes photo on each page
- [ ] **RG-03**: Report includes annotated plan snippet
- [ ] **RG-04**: Report includes camera symbol and viewing cone
- [ ] **RG-05**: Report includes annotation title and description
- [ ] **RG-06**: Report includes photo metadata (timestamp, camera, lens)
- [ ] **RG-07**: Report includes figure numbers
- [ ] **RG-08**: User can select A4 Portrait/Landscape or Letter layout

### Project Persistence

- [ ] **PP-01**: Project saves as JSON with external asset references
- [ ] **PP-02**: Project stores plans, photos, annotations, export settings, UI preferences
- [ ] **PP-03**: Project loads and restores all data correctly

### Performance (Basic)

- [ ] **PF-01**: Plan viewport interaction responds in <100ms
- [ ] **PF-02**: Smooth zoom and pan at standard project sizes

### Reliability (Basic)

- [ ] **RL-01**: Auto-save triggers every 2 minutes
- [ ] **RL-02**: Project can be recovered after crash

### Usability (Full)

- [ ] **US-01**: User can annotate a photo in ≤3 clicks
- [ ] **US-02**: Professional keyboard shortcuts (arrows, space, Ctrl+S, Ctrl+Z/Y, Delete)
- [ ] **US-03**: Dark mode
- [ ] **US-04**: Light mode

### Compatibility (macOS Only)

- [x] **CP-01**: Application runs natively on macOS (Apple Silicon + Intel)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Photo Browser

- **PHB-01**: User sees thumbnail grid of all photos
- **PHB-02**: User can sort photos by date, name, status, room
- **PHB-03**: User can filter by annotated/unannotated, exterior/interior

### Editing Enhancements

- **ED-05**: User can resize viewing cone
- **ED-06**: User can copy annotation
- **ED-07**: User can paste annotation

### Performance (Full)

- **PF-03**: Handle 1000+ photos
- **PF-04**: Handle 100+ plan pages
- **PF-05**: Fast loading for large projects

### Reliability (Full)

- **RL-03**: Crash recovery with backup restoration
- **RL-04**: Project backup on save

### Compatibility (Extended)

- **CP-02**: Windows 11 support
- **CP-03**: Windows 10 support
- **CP-04**: Linux support

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time chat / collaboration | High complexity, not core to documentation value |
| Video capture / playback | Storage/bandwidth costs, defer to v2+ |
| OAuth / social login | Email/password sufficient for v1 desktop app |
| Mobile app (iOS/Android) | Desktop-first, mobile later |
| 3D model support (IFC, Revit, SketchUp) | Future v2.0; scope creep for v1 |
| IFC/Revit/AutoCAD direct integration | Future v2.0; licensing complexity |
| Cloud synchronization | Future v2.0; infrastructure cost/complexity |
| Multi-user concurrent editing | Future v2.0; conflict resolution complexity |
| 360° photos / drone / thermal / point clouds | Future extensions; different capture workflow |
| Takeoff / measurement / estimating | Bluebeam owns this; not core value |
| Project management / scheduling / RFIs | Procore/Fieldwire territory; bloats app |
| BIM viewer / model coordination | Autodesk/Trimble territory; different product |
| Field capture / on-site photo taking | Desktop app; users import from camera/phone |
| Subscription licensing | Desktop users expect perpetual; competitive diff |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PM-01 | Phase 1 | Complete |
| PM-02 | Phase 1 | Complete |
| PM-03 | Phase 1 | Complete |
| PM-04 | Phase 1 | Complete |
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
| CP-01 | Phase 1 | Complete |

**Coverage:**

- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓

---
*Requirements defined: 2025-07-13*
*Last updated: 2025-07-13 after roadmap creation*
