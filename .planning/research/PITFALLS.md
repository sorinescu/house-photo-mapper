# Domain Pitfalls

**Domain:** Desktop Architectural Documentation App (Photo-to-Plan Annotation & PDF Report Generation)
**Researched:** 2025-07-13

---

## Critical Pitfalls

Mistakes that cause rewrites, major performance failures, or architectural instability.

### Pitfall 1: QGraphicsScene BSP Tree Degradation with Overlapping Annotation Items

**What goes wrong:** QGraphicsScene uses a BSP (Binary Space Partitioning) tree for spatial indexing. When many annotation items (camera markers, viewing cones, visible area polygons) overlap at the same coordinates — e.g., multiple photos taken from the same doorway — the BSP tree degrades from O(log n) to O(n) for insertion and hit-testing. Populating 1000+ overlapping items can take seconds instead of milliseconds.

**Why it happens:** The BSP tree partitions space assuming items are distributed. Overlapping items force deep tree traversal. Qt's "40000 Chips" demo works because chips don't overlap; architectural annotations cluster at doorways, corners, and room centers.

**Consequences:**
- Scene population blocks UI for 5-30 seconds on project load
- Hit-testing (click to select marker) becomes sluggish
- Zoom/pan stutters when many items overlap

**Prevention:**
- **Phase 3 (Plan Import & Annotation Layer):** Set `scene.setItemIndexMethod(QGraphicsScene.NoIndex)` for dynamic scenes with frequent item movement, or `BspTreeIndex` with fixed `bspTreeDepth` for static scenes
- **Phase 3:** Implement item recycling — reuse `QGraphicsItem` instances instead of remove/add cycles
- **Phase 3:** Cluster overlapping markers into a single "cluster item" at zoom levels < 25%; expand on zoom-in
- **Phase 3:** Set `scene.setSceneRect()` explicitly to avoid `itemsBoundingRect()` O(n) calls

**Detection:** Profile `scene.addItem()` loop time with 1000 items at same position. Watch for >500ms.

**Phase mapping:** Phase 3 (Plan Import & Annotation Layer), Phase 5 (Annotation Tools)

---

### Pitfall 2: ReportLab Platypus Exponential Slowdown on Multi-Page Reports

**What goes wrong:** ReportLab's `LongTable` and `BaseDocTemplate.build()` exhibit O(n²) behavior for reports with many pages (100+ photos → 50+ pages). Each page break triggers re-layout of the entire story. Large tables with auto-calculated row heights cause quadratic `CellStyle` creation.

**Why it happens:** Platypus's multi-pass layout (`multiBuild`) reflows the entire story for TOC, index, and page references. `LongTable.split()` creates new table copies with cumulative row data. `CellStyle.__init__` called per cell per split.

**Consequences:**
- 50-page report takes 10+ minutes instead of 30 seconds
- Memory spikes to 2-4 GB during generation
- UI freezes completely (single-threaded)

**Prevention:**
- **Phase 8 (Report Generation):** Split report into multiple small `Table` flowables (one per photo/page) instead of one `LongTable`
- **Phase 8:** Pre-calculate row heights; pass `rowHeights` to avoid auto-calculation
- **Phase 8:** Use `SimpleDocTemplate` with `build()` (single pass) not `multiBuild()` unless TOC needed
- **Phase 8:** Generate PDF in background `QThread` with progress signals; use `ProcessPoolExecutor` for parallel page rendering if needed
- **Phase 8:** Pre-load fonts once at startup; reuse `ParagraphStyle` objects

**Detection:** Profile `doc.build(story)` with 100 flowables. Time should scale linearly (~100ms/page). Quadratic = pitfall.

**Phase mapping:** Phase 8 (Report Generation)

---

### Pitfall 3: PDF Plan Scale Calibration Drift

**What goes wrong:** Imported PDF plans have no reliable scale metadata. Users calibrate by clicking two points on a dimension line. Clicking on dimension arrowheads (not endpoints) introduces ±100mm error at 1:100 scale. Cumulative dimensions vs. overall dimensions give different scales. "Scale to fit" PDF exports break nominal scale.

**Why it happens:** PDF is a visual format, not a CAD format. Dimension lines are graphics, not semantic measurements. Arrowhead width = 2mm on paper = 200mm at 1:100. Users click the visual center of arrowheads. Mixed-scale sheets (plan at 1:100, detail at 1:20) calibrate incorrectly if using sheet size.

**Consequences:**
- Camera positions offset by meters on large plans
- Viewing cones don't align with room geometry
- Generated reports show wrong distances → legal liability for surveyors/inspectors
- Users lose trust; "the software is inaccurate"

**Prevention:**
- **Phase 2 (Plan Import & Calibration):** Implement specification-based calibration: ask user for sheet size (A0-A4) and nominal scale, compute mathematically
- **Phase 2:** Verify calibration against a second known dimension far from the first; flag mismatch >1%
- **Phase 2:** Detect "scale to fit" exports by comparing PDF page size vs. declared sheet size
- **Phase 2:** Support mixed-scale sheets: let user define scale per page/viewport
- **Phase 5 (Annotation Tools):** Snap calibration clicks to dimension line endpoints (not arrowheads) using vector PDF parsing (PyMuPDF)

**Detection:** Calibrate same plan twice via different dimension lines. Results should match within 0.5%.

**Phase mapping:** Phase 2 (Plan Import & Calibration), Phase 5 (Annotation Tools)

---

### Pitfall 4: Photo Memory Explosion with 1000+ High-Res Images

**What goes wrong:** Loading 1000+ photos (12-48 MP each) into memory for thumbnails, EXIF extraction, and annotation previews causes OOM crashes or system swap thrashing. `QPixmap` cache default limit (10 MB) is useless for this workload.

**Why it happens:** `QPixmap` holds full decoded bitmap in RAM. 1000 × 24 MP × 4 bytes = 96 GB raw. Even thumbnails at 256px: 1000 × 256² × 4 = 256 MB minimum. EXIF parsing with `PIL.Image.open()` on 10k files blocks UI thread.

**Consequences:**
- App crashes on import (OOM killer)
- UI freezes for minutes during folder import
- Laptop fans spin; battery drains
- Cannot scroll photo browser smoothly

**Prevention:**
- **Phase 4 (Photo Import & Browser):** Implement tile-based lazy loading (like QPane): only decode visible thumbnails
- **Phase 4:** Use `QImageReader.setScaledSize()` to decode directly to thumbnail size — never load full res
- **Phase 4:** Background `QThreadPool` for EXIF extraction with progress signals; batch 50 at a time
- **Phase 4:** Implement virtual scrolling in photo browser (like `QListView` with `setUniformItemSizes`)
- **Phase 4:** Disk cache thumbnails as JPEG (quality 75) in project folder; invalidate on source mtime change
- **Phase 4:** Set `QPixmapCache.setCacheLimit(512*1024)` (512 MB) and use explicit keys for project-scoped caching

**Detection:** Import 2000 photos. Memory should stay < 2 GB. UI should remain responsive (<100ms scroll).

**Phase mapping:** Phase 4 (Photo Import & Browser), Phase 3 (Annotation Layer — photo preview pane)

---

### Pitfall 5: PySide6 QObject Memory Leaks via Lambda Slots and QRunnable

**What goes wrong:** Connecting lambdas to signals creates reference cycles. `QRunnable.setAutoDelete(False)` + Python reference prevents C++ deletion. `__del__` not called. Memory grows unbounded during long sessions (auto-save every 2 min, background thumbnail generation).

**Why it happens:** PySide6's `connect(lambda: ...)` doesn't increment lambda refcount properly in some versions. `QRunnable` with `autoDelete=False` expects manual cleanup but Python GC doesn't see C++ ownership. Bound methods as slots don't increment refcount; object deleted while slot still connected → segfault on signal emission.

**Consequences:**
- Memory leak: 50-200 MB/hour of use
- Random crashes on auto-save or project close
- "Ghost" signals fire on deleted objects → corrupted project state

**Prevention:**
- **Phase 0 (Project Setup & Architecture):** Use `@Slot()` decorated methods on `QObject` subclasses only — never lambdas for long-lived connections
- **Phase 0:** For one-shot async tasks, use `QObject` wrapper with `deleteLater()` in `finished` signal
- **Phase 0:** `QRunnable` → always `setAutoDelete(True)`; communicate results via signal from a `QObject` worker, not the runnable itself
- **Phase 0:** Set parent on every `QObject`/`QWidget`; rely on Qt parent-child deletion
- **Phase 0:** Run `gc.collect()` periodically in background; monitor `QObject` count in debug builds

**Detection:** Run 4-hour soak test with auto-save every 2 min. Memory growth should be < 50 MB total.

**Phase mapping:** Phase 0 (Project Setup & Architecture), all phases (cross-cutting)

---

### Pitfall 6: Coordinate System Mismatch Between Plan (World), Screen (View), and Image (Photo) Spaces

**What goes wrong:** Camera position stored in plan coordinates (meters, Y-up). Viewport uses screen coordinates (pixels, Y-down). Photo EXIF orientation rotates image data but not annotation overlay. Viewing cone drawn in wrong quadrant. Export to PDF places markers at wrong positions.

**Why it happens:** Three coordinate systems: WORLD (architectural, Y-up, meters), SCREEN (Qt, Y-down, pixels), IMAGE (EXIF, Y-down, pixels, 8 orientations). Implicit conversions lose precision or flip axes. `QGraphicsView.mapToScene()` / `mapFromScene()` only handles SCREEN↔WORLD. IMAGE space requires EXIF-aware transform.

**Consequences:**
- Viewing cone points 90° or 180° off
- Camera marker snaps to wrong wall
- PDF report shows photo in wrong room
- "It works on my plan" but fails on rotated/flipped imports

**Prevention:**
- **Phase 1 (Core Architecture & Data Model):** Define explicit `CoordinateSystem` enum: `WORLD`, `SCREEN`, `IMAGE`, `PDF`
- **Phase 1:** Central `CoordinateConverter` with registered `Transform2D` (scale, rotation, translation, Y-flip)
- **Phase 1:** All geometry objects carry `CoordinateSystem` tag; arithmetic between mismatched systems raises `CRSMismatchError`
- **Phase 1:** EXIF orientation applied at load time → normalize to `IMAGE` space (Y-down, 0° rotation); store transform to `WORLD`
- **Phase 3/5:** Annotation tools work in `WORLD`; view transforms to `SCREEN` only at paint time

**Detection:** Import plan, add camera at (10, 10) facing 90°. Rotate plan 90°. Camera should visually stay at same physical location. Export PDF → verify marker position.

**Phase mapping:** Phase 1 (Core Architecture & Data Model), Phase 3 (Plan Import), Phase 5 (Annotation Tools), Phase 8 (Report Generation)

---

## Moderate Pitfalls

Issues that cause significant rework or user frustration if not addressed early.

### Pitfall 7: UI Freeze on Large .ui File Load (Qt Designer Generated Code)

**What goes wrong:** Single `.ui` file with 50+ widgets (main window, toolbars, dock panels, dialogs) takes 1-2 seconds to `setupUi()`, freezing splash screen. User sees "Not Responding."

**Why it happens:** `pyside6-uic` generates one massive `setupUi()` creating all widgets sequentially. Qt widget construction is slow in Python. All dialogs instantiated at startup even if never used.

**Prevention:**
- **Phase 0:** Split UI into multiple `.ui` files per dock panel/dialog
- **Phase 0:** Lazy-load dialogs: instantiate only when first shown (use `QUiLoader` or manual factory)
- **Phase 0:** Show `QSplashScreen` with progress *before* `setupUi()`; process events during load
- **Phase 0:** Consider hand-written UI for performance-critical windows (photo browser, plan view)

**Phase mapping:** Phase 0 (Project Setup & Architecture)

---

### Pitfall 8: PySide6 Enum Attribute Lookup Overhead in Hot Paths

**What goes wrong:** `Qt.AlignmentFlag.AlignCenter` looked up thousands of times per frame during paint/delegate/model access. `PyObject_GetAttr` on the massive `Qt` namespace adds measurable overhead.

**Why it happens:** `Qt` module aggregates all enums. `Qt.AlignCenter` → dict lookup in giant module. In `QAbstractItemModel.data()` called for every visible cell (100s × roles), this adds up.

**Prevention:**
- **Phase 0:** Use fully qualified enums: `Qt.AlignmentFlag.AlignCenter`, `Qt.ItemDataRole.DisplayRole`
- **Phase 0:** Cache enum values as module-level constants: `DISPLAY_ROLE = Qt.ItemDataRole.DisplayRole`
- **Phase 0:** In paint delegates, use `option.palette.color(QPalette.ColorRole.WindowText)` not `Qt.GlobalColor.black`

**Phase mapping:** Phase 0, Phase 3 (Model/View for photo browser), Phase 4

---

### Pitfall 9: Annotation Undo/Redo Stack Corruption with Composite Commands

**What goes wrong:** Moving a camera marker updates position, rotation, viewing cone, visible area polygon, and associated photo link. If each is a separate `QUndoCommand`, undo reverses in wrong order → cone detaches from marker, photo link breaks. Redo reapplies inconsistently.

**Why it happens:** `QUndoStack` treats each `push()` as atomic. Composite operations need a parent `QUndoCommand` with children. Child `undo()`/`redo()` order must be reverse of creation.

**Prevention:**
- **Phase 6 (Editing & Undo/Redo):** Implement `CompositeCommand` that groups child commands
- **Phase 6:** Each annotation tool action creates one composite: `MoveMarkerCommand` contains `MovePositionCommand`, `UpdateConeCommand`, `UpdateVisibleAreaCommand`, `UpdatePhotoLinkCommand`
- **Phase 6:** Test undo/redo after every tool action; verify object graph integrity

**Phase mapping:** Phase 6 (Editing & Undo/Redo)

---

### Pitfall 10: PDF Export LayoutError — Flowable Too Large for Frame

**What goes wrong:** ReportLab raises `LayoutError: More than 10 pages generated without content` when a photo + caption + plan excerpt flowable exceeds frame height. Happens with large photos on A4 portrait, or long annotation text.

**Why it happens:** Platypus cannot split `Image` flowables. If `Image` + `Paragraph` > frame height, it tries new page, but same flowable still doesn't fit → infinite loop of empty pages.

**Prevention:**
- **Phase 8:** Pre-scale images to fit frame: `max_height = frame_height - caption_space`; use `Image(..., height=max_height, kind='proportional')`
- **Phase 8:** Wrap photo+caption in `KeepTogether` but set `splitLongTables=True` equivalent for custom flowables
- **Phase 8:** Implement custom `PhotoReportFlowable` that splits across pages (photo on page N, caption on page N+1 if needed)
- **Phase 8:** Test with A4, Letter, A3, custom sizes; landscape and portrait

**Phase mapping:** Phase 8 (Report Generation)

---

### Pitfall 11: Auto-Save Corrupts Project File During Active Editing

**What goes wrong:** Auto-save timer fires while user is dragging a marker. JSON serializer captures half-updated model (position changed, but viewing cone not yet updated). On crash recovery, project loads with inconsistent state.

**Why it happens:** Auto-save runs on main thread (or background thread without proper snapshot). Model is mutable during drag. No transaction boundary.

**Prevention:**
- **Phase 7 (Project Persistence):** Implement copy-on-write snapshot: `project.create_snapshot()` deep-copies model to immutable dict; auto-save writes snapshot
- **Phase 7:** Use `QUndoStack`'s `cleanChanged` signal — only auto-save when stack is clean (no active command)
- **Phase 7:** Write to temp file + atomic rename (`os.replace()`) to avoid partial writes
- **Phase 7:** Include version + checksum in project file; validate on load

**Phase mapping:** Phase 7 (Project Persistence)

---

### Pitfall 12: Multi-Page PDF Plan Import Loses Page-to-Floor Mapping

**What goes wrong:** User imports 10-page PDF (5 floors × 2 plans each). App treats all pages as one plan or loses floor association. User must manually assign each page to a floor.

**Why it happens:** PDF has no semantic floor metadata. Page order ≠ floor order (basement may be last). Architect's sheet numbering (A101, A102, A201) not parsed.

**Prevention:**
- **Phase 2:** Parse PDF text layer for sheet numbers/names (PyMuPDF `page.get_text()`)
- **Phase 2:** Present page thumbnails with auto-detected floor labels; let user confirm/reorder via drag-drop
- **Phase 2:** Store `page_index → floor_id` mapping in project; persist in JSON
- **Phase 2:** Support multi-page TIFF/PNG sequences similarly

**Phase mapping:** Phase 2 (Plan Import & Calibration)

---

## Minor Pitfalls

Nuisances that degrade polish but don't break core workflow.

### Pitfall 13: Dark Mode Breaks Annotation Visibility

**What goes wrong:** Camera markers (red), viewing cones (blue), visible areas (green) use hardcoded colors. In dark mode, low-contrast colors become invisible on dark plan backgrounds.

**Prevention:**
- **Phase 3/9 (UI Polish):** Use semantic color roles: `QPalette.ColorRole.Highlight`, `QPalette.ColorRole.Text`, custom `AnnotationRole` palette
- **Phase 3/9:** Define annotation colors in theme-aware stylesheet; test both light/dark

**Phase mapping:** Phase 9 (UI Polish & Shortcuts)

---

### Pitfall 14: Keyboard Shortcut Conflicts with Qt Defaults

**What goes wrong:** `Ctrl+S` (save) works, but `Space` (pan) conflicts with `QAbstractButton` activation. `Delete` key doesn't work when focus is in photo browser list. `Ctrl+Z` undo doesn't trigger if focus in line edit.

**Prevention:**
- **Phase 9:** Install `QShortcut` on main window with `Qt.ShortcutContext.ApplicationShortcut`
- **Phase 9:** Use `QAction` with `setShortcutContext(Qt.ApplicationShortcut)` for all global shortcuts
- **Phase 9:** Implement `eventFilter` on viewport for pan/zoom keys regardless of focus

**Phase mapping:** Phase 9 (UI Polish & Shortcuts)

---

### Pitfall 15: HEIC/HEIF Import Fails on Windows/Linux Without Codecs

**What goes wrong:** User drags iPhone photos (HEIC). `PIL.Image.open()` raises `UnidentifiedImageError` or returns garbage. No fallback.

**Prevention:**
- **Phase 4:** Bundle `pillow-heif` plugin; register opener at startup
- **Phase 4:** Detect missing codec; show friendly dialog: "Install HEIF support?" with link to Microsoft Store / `apt install libheif`
- **Phase 4:** Graceful degradation: skip unreadable files, log, continue import

**Phase mapping:** Phase 4 (Photo Import & Browser)

---

### Pitfall 16: ReportLab Font Substitution Breaks Unicode in Annotations

**What goes wrong:** User enters room name "Büro" or "会议室". ReportLab built-in fonts (Helvetica) don't support Unicode. PDF shows □□□ or missing glyphs.

**Prevention:**
- **Phase 8:** Register TTF fonts (DejaVu Sans, Noto Sans) at startup; use as default for all `ParagraphStyle`
- **Phase 8:** Embed fonts in PDF (ReportLab does by default for TTF)
- **Phase 8:** Test with CJK, Arabic, emoji in annotation text

**Phase mapping:** Phase 8 (Report Generation)

---

### Pitfall 17: Navigator/Overview Widget Performance Death Spiral

**What goes wrong:** Mini-map (navigator) updates on every scroll/zoom of main view. With 1000+ annotation items, each update triggers full scene `items()` call → UI thread stalls.

**Why it happens:** Navigator connected to `QGraphicsView.scrollContentsBy` / `viewport()` signals without throttling. Each update iterates all items to draw bounding boxes.

**Prevention:**
- **Phase 3/9:** Throttle navigator updates: `QTimer.singleShot(50, update_navigator)` coalesces rapid scrolls
- **Phase 3/9:** Navigator draws simplified representation (floor outline only, no annotations) at zoomed-out scale
- **Phase 3/9:** Use `QGraphicsScene.setItemIndexMethod(NoIndex)` for navigator scene (static, few items)

**Phase mapping:** Phase 3 (Plan Import & Annotation Layer), Phase 9 (UI Polish)

---

## Phase-Specific Warning Summary

| Phase | Primary Pitfalls to Address |
|-------|----------------------------|
| **0** Project Setup | PySide6 memory model (Pitfall 5), Enum performance (Pitfall 8), UI loading (Pitfall 7) |
| **1** Core Architecture | Coordinate system design (Pitfall 6), Data model immutability for snapshots (Pitfall 11) |
| **2** Plan Import | Scale calibration (Pitfall 3), Multi-page floor mapping (Pitfall 12) |
| **3** Plan Annotation Layer | QGraphicsScene BSP degradation (Pitfall 1), Navigator performance (Pitfall 17) |
| **4** Photo Import | Memory explosion (Pitfall 4), HEIC support (Pitfall 15), EXIF threading |
| **5** Annotation Tools | Coordinate conversion (Pitfall 6), Snap-to-dimension calibration (Pitfall 3) |
| **6** Editing & Undo | Composite command design (Pitfall 9) |
| **7** Project Persistence | Atomic auto-save (Pitfall 11), Versioned JSON schema |
| **8** Report Generation | ReportLab O(n²) (Pitfall 2), LayoutError (Pitfall 10), Fonts (Pitfall 16) |
| **9** UI Polish | Dark mode (Pitfall 13), Shortcuts (Pitfall 14), Navigator (Pitfall 17) |
| **10** Performance | All perf pitfalls integration test |
| **11** Packaging | PyInstaller binary size, DLL hell (PyMuPDF, OpenCV), macOS codesign |
| **12** Documentation | User guide for calibration workflow (Pitfall 3), Troubleshooting perf |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| QGraphicsScene performance | HIGH | Verified via Qt forums, QPane architecture, 40000 chips issue |
| ReportLab scaling | HIGH | Multiple StackOverflow/ReportLab mailing list reports with workarounds |
| PDF scale calibration | HIGH | Architectural forum discussions, SketchUp calibration blog, PDF-to-CAD pitfalls |
| PySide6 memory/lambda | MEDIUM | Forum discussions, some version-specific; mitigate defensively |
| Coordinate system design | MEDIUM | Based on archit-app patterns; needs validation in implementation |
| Photo memory management | HIGH | QPane tile-based approach proven; standard image viewer pattern |
| Auto-save corruption | MEDIUM | General pattern; project-specific validation needed |

---

## Gaps Requiring Phase-Specific Research

1. **Phase 10 (Performance):** Need empirical benchmarks for 1000 photos + 100 plan pages on target hardware (M1/M2 Mac, Windows laptop). Define "smooth" thresholds (60 fps pan/zoom, <100ms annotation place).

2. **Phase 8 (Report Generation):** Test ReportLab vs. WeasyPrint vs. `pdfme` for this specific layout (photo + mini-plan + metadata per page). ReportLab programmatic control vs. HTML/CSS flexibility.

3. **Phase 11 (Packaging):** PyInstaller + PyMuPDF + OpenCV + PySide6 binary size and startup time on macOS/Windows. Code signing / notarization pipeline.

4. **Phase 2 (Calibration):** Investigate PyMuPDF vector parsing for automatic dimension line detection to assist calibration (snap to dimension endpoints).

5. **Phase 6 (Undo/Redo):** Research `QUndoCommand` serialization for crash recovery (replay command stack from last clean save).