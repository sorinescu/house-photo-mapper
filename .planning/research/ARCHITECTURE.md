# Architecture Patterns

**Domain:** Desktop Architectural Documentation Application
**Researched:** 2026-07-13

---

## Recommended Architecture

### High-Level Architecture: MVVM with Qt Signal/Slot Event Bus

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  MainWindow │  │  ProjectVM  │  │  PlanViewVM │  │ PhotoBrowser│        │
│  │   (View)    │  │             │  │             │  │    VM       │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┼────────────────┼────────────────┘               │
│                          ▼                                                │
│              ┌───────────────────────┐                                   │
│              │   Qt Signal/Slot      │                                   │
│              │   Event Bus           │ ◄── Decoupled communication       │
│              └───────────┬───────────┘                                   │
│                          │                                               │
│         ┌────────────────┼────────────────┐                               │
│         ▼                ▼                ▼                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                       │
│  │ Project     │  │ Plan        │  │ Photo       │                       │
│  │ Model       │  │ Model       │  │ Model       │                       │
│  │ (JSON/SQLite)│  │ (QGraphics) │  │ (Metadata)  │                       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                       │
│         │                │                │                               │
└─────────┼────────────────┼────────────────┼───────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INFRASTRUCTURE LAYER                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Persistence  │ │ PDF Engine   │ │ Image Cache  │ │ Report       │       │
│  │ Service      │ │ (PyMuPDF)    │ │ (Thumbnails) │ │ Generator    │       │
│  │ (JSON/SQLite)│ │              │ │              │ │ (ReportLab)  │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **MainWindow (View)** | Top-level window, menu bar, toolbars, docking | ProjectVM, PlanViewVM, PhotoBrowserVM via signals |
| **ProjectVM** | Project lifecycle (new, open, save, auto-save), undo/redo stack coordination | PersistenceService, PlanModel, PhotoModel |
| **PlanViewVM** | Plan viewport state (zoom, pan, current floor), annotation tools, PDF rendering coordination | PlanModel, QGraphicsScene, ProjectVM |
| **PhotoBrowserVM** | Photo library management, filtering, sorting, metadata extraction | PhotoModel, ImageCacheService |
| **AnnotationVM** | Camera marker, arrow, cone, polygon creation/editing, serialization | PlanModel (QGraphicsScene), UndoStack |
| **ReportVM** | Report template selection, layout composition, PDF generation coordination | ReportGenerator, ProjectModel, PlanModel, PhotoModel |
| **ProjectModel** | Central data model: plans, photos, annotations, settings, export config | PersistenceService (JSON), all ViewModels |
| **PlanModel** | Multi-page PDF management, page rendering, coordinate transforms | PyMuPDF, QGraphicsScene |
| **PhotoModel** | Photo metadata (EXIF), file management, duplicate detection, thumbnails | Pillow/OpenCV, ImageCacheService |
| **PersistenceService** | Project serialization (JSON + external assets), auto-save, crash recovery | ProjectModel, FileSystem |
| **PDF Engine (PyMuPDF)** | PDF rendering, page extraction, text/metadata extraction | PlanModel, ReportGenerator |
| **Image Cache** | Thumbnail generation, LRU memory cache, disk cache | PhotoBrowserVM, PlanViewVM (for photo preview) |
| **Report Generator (ReportLab)** | Professional PDF report composition, pagination, figure numbering | ReportVM, ProjectModel |

---

### Data Flow

#### 1. Project Load Flow
```
User → MainWindow.openProject() 
    → ProjectVM.loadProject(path)
    → PersistenceService.readJSON(path)
    → ProjectModel.deserialize(data)
    → PlanModel.loadPDFs() + PhotoModel.loadPhotos()
    → PlanViewVM.onPlansLoaded() + PhotoBrowserVM.onPhotosLoaded()
    → Views update via ModelView binding
```

#### 2. Photo Annotation Flow
```
User clicks PlanView → PlanViewVM.startAnnotationTool()
    → PlanViewVM.createCameraMarker(position, floor)
    → AnnotationVM.createMarker() → QGraphicsScene.addItem()
    → AnnotationVM.onMarkerCreated(marker)
    → ProjectModel.addAnnotation(marker)
    → ProjectVM.markDirty() → auto-save triggered
```

#### 3. Report Generation Flow
```
User → ReportVM.generateReport(settings)
    → ReportGenerator.composeReport(ProjectModel)
    → For each annotation: render plan snippet + photo + metadata
    → ReportLab builds PDF pages with figure numbers, TOC
    → Progress signals → ReportVM.progressUpdated(percent)
    → Complete → ReportVM.reportReady(outputPath)
```

#### 4. Photo Import Flow
```
User → PhotoBrowserVM.importPhotos(paths)
    → PhotoModel.extractMetadata(paths) [background thread]
    → PhotoModel.detectDuplicates() [perceptual hash]
    → ImageCacheService.generateThumbnails() [background]
    → PhotoBrowserVM.photosImported(list)
    → ProjectModel.addPhotos() → ProjectVM.markDirty()
```

---

## Patterns to Follow

### Pattern 1: MVVM with Qt Signal/Slot as Event Bus
**What:** ViewModels expose Qt Properties (`@Property`) and Signals (`pyqtSignal`). Views bind via `QDataWidgetMapper` or manual signal connections. Models are pure Python data classes with no Qt dependencies.

**When:** All UI-bound state. Enables testable ViewModels (mock signals), designer-friendly Views (Qt Designer), and clean separation.

**Example:**
```python
# viewmodels/plan_view_vm.py
class PlanViewModel(QObject):
    currentFloorChanged = Signal(int)
    zoomLevelChanged = Signal(float)
    annotationToolChanged = Signal(str)
    
    def __init__(self, plan_model: PlanModel, project_vm: ProjectViewModel):
        super().__init__()
        self._model = plan_model
        self._project_vm = project_vm
        self._current_floor = 0
        self._zoom = 1.0
        self._tool = "select"
    
    @Property(int, notify=currentFloorChanged)
    def currentFloor(self): return self._current_floor
    
    @currentFloor.setter
    def currentFloor(self, value):
        if self._current_floor != value:
            self._current_floor = value
            self.currentFloorChanged.emit(value)
            self._model.setCurrentPage(value)
```

### Pattern 2: QGraphicsScene for Vector Annotations
**What:** Each plan page = one `QGraphicsScene`. Annotations are custom `QGraphicsItem` subclasses (CameraMarker, ViewingCone, VisibleAreaPolygon, Label). Scene handles selection, drag, rotation, z-order natively.

**When:** Interactive 2D annotation overlay on raster PDF backgrounds. Performant for 1000+ items with BSP index.

**Example:**
```python
# models/annotation_items.py
class CameraMarker(QGraphicsEllipseItem):
    def __init__(self, x, y, radius=8):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setBrush(QBrush(QColor("#FF3B30")))
        self.setPen(QPen(Qt.white, 2))
        self._viewing_cone = None
    
    def itemChange(self, change, value):
        if change == ItemPositionChange and self._viewing_cone:
            self._viewing_cone.updateFromMarker(value)
        return super().itemChange(change, value)
    
    def to_dict(self) -> dict:
        pos = self.scenePos()
        return {"type(self)
            "x": pos.x(), "y": pos.y(),
            "cone_angle": self._viewing_cone.angle if self._viewing_cone else 45,
            "cone_direction": self._viewing_cone.rotation if self._viewing_cone else 0,
        }
```

### Pattern 3: Background Worker Pattern with QThreadPool
**What:** CPU-intensive operations (PDF rendering, thumbnail generation, EXIF extraction, duplicate detection) run in `QRunnable` workers via `QThreadPool.globalInstance()`. Progress/signals via `QObject` worker signals.

**When:** Any operation >50ms that would block the UI thread.

**Example:**
```python
# services/image_cache.py
class ThumbnailWorkerSignals(QObject):
    finished = Signal(str, QPixmap)  # path, pixmap
    progress = Signal(int, int)      # current, total

class ThumbnailWorker(QRunnable):
    def __init__(self, paths: List[str], size: QSize):
        super().__init__()
        self.paths = paths
        self.size = size
        self.signals = ThumbnailWorkerSignals()
    
    def run(self):
        for i, path in enumerate(self.paths):
            pixmap = self._generate_thumbnail(path, self.size)
            self.signals.finished.emit(path, pixmap)
            self.signals.progress.emit(i + 1, len(self.paths))

# Usage in PhotoBrowserVM
def generate_thumbnails(self, paths):
    worker = ThumbnailWorker(paths, QSize(256, 256))
    worker.signals.finished.connect(self._on_thumbnail_ready)
    worker.signals.progress.connect(self._on_thumbnail_progress)
    QThreadPool.globalInstance().start(worker)
```

### Pattern 4: Command Pattern for Undo/Redo
**What:** Every user action that mutates model state = a `QUndoCommand` subclass. Commands know how to `redo()` and `undo()`. Central `QUndoStack` owned by ProjectVM.

**When:** All editing operations (move marker, rotate cone, delete annotation, change photo tags).

**Example:**
```python
# commands/annotation_commands.py
class MoveMarkerCommand(QUndoCommand):
    def __init__(self, marker: CameraMarker, old_pos: QPointF, new_pos: QPointF):
        super().__init__(f"Move marker {marker.id}")
        self._marker = marker
        self._old_pos = old_pos
        self._new_pos = new_pos
    
    def redo(self): self._marker.setPos(self._new_pos)
    def undo(self): self._marker.setPos(self._old_pos)
    
    def id(self): return 1001  # for command compression
    def mergeWith(self, other):
        if other.id() == 1001 and other._marker is self._marker:
            self._new_pos = other._new_pos
            return True
        return False
```

### Pattern 5: JSON Project Format with External Assets
**What:** Project file (`.hpmproj`) = JSON manifest with references. Photos and PDFs stored as external files in project folder (`assets/photos/`, `assets/plans/`). Enables version control, partial loads, external tool access.

**When:** Project persistence, auto-save, sharing.

**Example:**
```json
{
  "version": 1,
  "project": {
    "name": "123 Main St Documentation",
    "created": "2026-07-13T10:30:00Z",
    "modified": "2026-07-13T14:22:00Z",
    "settings": { "units": "metric", "paper_size": "A4" }
  },
  "plans": [
    { "id": "plan_1", "file": "assets/plans/ground_floor.pdf", "page_count": 1, "dpi": 300 },
    { "id": "plan_2", "file": "assets/plans/first_floor.pdf", "page_count": 1, "dpi": 300 }
  ],
  "photos": [
    { "id": "photo_1", "file": "assets/photos/IMG_001.jpg", "exif": {...}, "hash": "a1b2c3..." },
    { "id": "photo_2", "file": "assets/photos/IMG_002.jpg", "exif": {...}, "hash": "d4e5f6..." }
  ],
  "annotations": [
    { "id": "ann_1", "plan_id": "plan_1", "photo_id": "photo_1", 
      "type": "camera", "x": 1250, "y": 890, "floor": 0,
      "cone_angle": 45, "cone_direction": 90,
      "title": "Living Room", "description": "Main view from entrance" }
  ],
  "report_settings": { "template": "standard", "include_toc": true }
}
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: God ViewModel
**What:** Single ViewModel handling project, plans, photos, annotations, reports.
**Why bad:** 2000+ lines, untestable, tight coupling, merge conflicts.
**Instead:** One ViewModel per conceptual screen/domain (ProjectVM, PlanViewVM, PhotoBrowserVM, AnnotationVM, ReportVM). Communicate via signals.

### Anti-Pattern 2: Embedding Business Logic in QGraphicsItem
**What:** `CameraMarker` directly modifies `ProjectModel` or triggers saves.
**Why bad:** Items become untestable, circular dependencies, violates separation.
**Instead:** Items emit signals (`positionChanged`, `rotationChanged`). ViewModel connects and updates Model.

### Anti-Pattern 3: Blocking PDF Rendering on UI Thread
**What:** `QPixmap = pdf_page.renderToImage()` called in paint event or button handler.
**Why bad:** UI freezes for 100-500ms per page at 300 DPI.
**Instead:** Pre-render pages to tiles in background worker. Cache rendered tiles. View shows cached tiles instantly.

### Anti-Pattern 4: Storing Absolute Paths in Project JSON
**What:** `"file": "/Users/sorin/Projects/house/IMG_001.jpg"`
**Why bad:** Breaks on move, different OS, different user.
**Instead:** Relative paths from project root: `"file": "assets/photos/IMG_001.jpg"`. Resolve at load time.

### Anti-Pattern 5: Direct Model-to-View Coupling
**What:** `PlanModel` holds reference to `QGraphicsScene` or `PlanView`.
**Why bad:** Model can't be tested headless, can't reuse for report generation.
**Instead:** Model is pure data. ViewModel adapts Model → View. ReportGenerator uses Model directly.

---

## Scalability Considerations

| Concern | At 100 photos / 10 plans | At 1000 photos / 50 plans | At 5000 photos / 200 plans |
|---------|--------------------------|---------------------------|----------------------------|
| **Photo Thumbnails** | In-memory cache OK | LRU memory + disk cache | Disk cache + on-demand generation |
| **PDF Rendering** | Render all pages on load | Render visible + adjacent | Tile-based rendering, progressive |
| **Annotation Items** | Single scene per plan | Scene per plan, virtualize | Scene per plan, item clustering |
| **Project Load Time** | <2s (JSON + metadata) | 3-5s (lazy load thumbnails) | 5-10s (background indexing) |
| **Memory Usage** | ~500MB | ~1.5GB | ~3GB (requires 64-bit) |
| **Undo Stack** | Unlimited in memory | Limit to 100 commands | Limit + periodic compression |

### Scalability Patterns to Implement Incrementally

1. **Phase 1-3 (MVP):** Simple in-memory caches, render all plan pages on load
2. **Phase 4-6:** Add LRU memory cache + disk cache for thumbnails; background PDF tile rendering
3. **Phase 7-9:** Virtualized photo browser (QListView + custom model), plan page lazy loading
4. **Phase 10+:** SQLite index for metadata search, memory-mapped project format for huge projects

---

## Build Order Implications

Based on component dependencies, the recommended phase ordering:

```
Phase 0: Project Setup
    └── pyproject.toml, CI, linting, basic PySide6 app scaffold

Phase 1: Core Infrastructure (Foundation)
    ├── PersistenceService (JSON read/write)
    ├── ProjectModel (data classes)
    ├── ProjectVM (project lifecycle)
    └── MainWindow (empty shell with menu/dock widgets)

Phase 2: Plan System
    ├── PlanModel (PDF loading via PyMuPDF)
    ├── PlanViewVM (viewport, floor switching)
    ├── PlanView (QGraphicsView + QGraphicsScene)
    └── PDF page rendering (background worker)

Phase 3: Photo System
    ├── PhotoModel (metadata, EXIF, duplicates)
    ├── PhotoBrowserVM (filter, sort, thumbnails)
    ├── PhotoBrowserView (QListView + delegate)
    └── ImageCacheService (thumbnail generation)

Phase 4: Annotation System
    ├── Annotation items (CameraMarker, ViewingCone, VisibleArea, Label)
    ├── AnnotationVM (tool state, creation, editing)
    ├── Undo/Redo stack (QUndoStack + commands)
    └── PlanView integration (tool toolbar, shortcuts)

Phase 5: Project Persistence Integration
    ├── Full project save/load (plans + photos + annotations)
    ├── Auto-save (2-min timer + dirty flag)
    ├── Crash recovery (backup files)
    └── Recent projects menu

Phase 6: Report Generation
    ├── ReportVM (template selection, settings)
    ├── ReportGenerator (ReportLab composition)
    ├── Plan snippet rendering (QGraphicsScene → QImage)
    └── PDF output with TOC, figure numbers

Phase 7: Polish & Performance
    ├── Keyboard shortcuts (full professional set)
    ├── Dark/Light theme (QSS)
    ├── Performance profiling + optimization
    └── Memory pressure handling

Phase 8: Packaging & Distribution
    ├── PyInstaller spec (macOS .app, Windows .exe)
    ├── Code signing / notarization
    ├── Auto-update framework (Sparkle/WinSparkle)
    └── DMG/MSI installer creation

Phase 9: Documentation & Testing
    ├── User guide (PDF + built-in help)
    ├── Automated UI tests (pytest-qt)
    ├── Performance benchmarks
    └── Accessibility audit
```

**Key Dependency Rule:** Phase N+1 only depends on completed Phase N interfaces. ViewModels define the contract; Views and Models can evolve independently behind stable ViewModel APIs.

---

## Sources

- Qt Model/View Architecture: https://doc.qt.io/qt-6/model-view-programming.html
- PySide6 MVVM Examples: https://github.com/ericjameszimmerman/pyside6-mvvm-example
- MVVM Pattern for PyQt/PySide: https://medium.com/@mark_huber/a-clean-architecture-for-a-pyqt-gui-using-the-mvvm-pattern-b8e5d9ae833d
- QGraphicsScene Documentation: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsScene.html
- QGraphicsView Framework Tutorial: https://www.pythonguis.com/tutorials/pyside6-qgraphics-vector-graphics/
- Qt Undo Framework: https://doc.qt.io/qt-6/undoframework.html
- Construction Photo Documentation Software Market Analysis: PlanRadar, OpenSpace, Buildbite, CompanyCam (2024-2026)
- Architectural Documentation Standards: AEC UK BIM Standards, ISO 19650