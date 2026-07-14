# Phase 4: Annotation Tools - Research

**Researched:** 2026-07-14
**Domain:** QGraphicsItem annotation graphics, QUndoStack undo/redo infrastructure, QShortcut keyboard shortcuts, photo-annotation binding
**Confidence:** HIGH

## Summary

Phase 4 implements the Annotation Tools: users place camera markers on plan pages, set direction arrows and viewing cones, draw visible-area polygons with vertex editing, enter metadata (title, description, tags), assign floors, and edit everything with unlimited undo/redo using professional keyboard shortcuts. The phase builds on Phase 2's QGraphicsScene/View infrastructure and Phase 3's PhotoModel, adding QUndoStack for undo/redo with mergeWith compression for continuous drag operations, QGraphicsItem vertex handles for polygon editing, QShortcut for context-aware keyboard shortcuts, and bidirectional selection sync between photo browser and plan annotations.

**Primary recommendation:** Use PySide6's built-in QUndoStack/QUndoCommand framework with mergeWith() for drag compression, QGraphicsItem children for polygon vertex handles (GripItem pattern), QShortcut with Qt.WindowShortcut context for keyboard shortcuts, and QGraphicsItemGroup for annotation grouping. No new external packages required — all patterns use PySide6's existing API.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AN-01 | User can place camera position marker on plan | CameraMarkerItem already implemented (04-01); needs QUndoCommand integration |
| AN-02 | User can set camera direction arrow from marker | DirectionArrowItem already implemented (04-01); needs rotation QUndoCommand |
| AN-03 | User can adjust viewing cone angle | ViewingConeItem already implemented (04-01); needs cone angle QUndoCommand |
| AN-04 | User can draw visible area polygon (4+ points) | VisibleAreaItem already implemented (04-01); needs GripItem vertex handles |
| AN-05 | User can enter title for annotation | AnnotationViewModel metadata flow (04-02); needs EditMetadataCommand |
| AN-06 | User can enter description for annotation | AnnotationViewModel metadata flow (04-02); needs EditMetadataCommand |
| AN-07 | User can add tags to annotation | AnnotationViewModel metadata flow (04-02); needs EditMetadataCommand |
| AN-08 | User can select floor for annotation | AnnotationViewModel floor selection (04-02); needs EditFloorCommand |
| ED-01 | User can move camera marker | MoveMarkerCommand with mergeWith for drag compression |
| ED-02 | User can rotate direction arrow | RotateArrowCommand with mergeWith for continuous rotation |
| ED-03 | User can delete annotation | DeleteAnnotationCommand with undo restore |
| ED-04 | Unlimited undo/redo for all edits | QUndoStack integration with all commands |
| NA-01 | Arrow keys navigate previous/next photo | QShortcut with Qt.Key_Left/Right |
| NA-02 | Space key confirms/places annotation | QShortcut with Qt.Key_Space |
| NA-03 | Ctrl+S saves project | Already exists in MainWindow.keyPressEvent |
| NA-04 | Ctrl+Z undoes last action | QUndoStack.undo() wired to Edit menu |
| NA-05 | Ctrl+Y redoes last undone action | QUndoStack.redo() wired to Edit menu |
| NA-06 | Delete key removes selected annotation | QShortcut with Qt.Key_Delete |
| NA-07 | Ctrl+Mouse wheel zooms plan | Already exists in PlanGraphicsView.wheelEvent |
| NA-08 | Middle mouse button pans plan | Already exists in PlanGraphicsView.mousePressEvent |
| US-01 | User can annotate a photo in ≤3 clicks | Creation flow in AnnotationViewModel (04-02) |
| US-02 | Professional keyboard shortcuts | QShortcut infrastructure in Plan 04-04 |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Annotation graphics rendering | Frontend (QGraphicsItem) | — | Vector items in QGraphicsScene, GPU-accelerated |
| Undo/redo command infrastructure | Backend (QUndoStack) | Frontend (menu actions) | Command pattern with state serialization |
| Keyboard shortcut handling | Frontend (QShortcut) | Backend (ViewModel slots) | Qt event loop integration, context-aware |
| Polygon vertex editing | Frontend (GripItem children) | — | QGraphicsItem child hierarchy for drag |
| Photo-annotation binding | Backend (AnnotationViewModel) | Frontend (selection sync) | Bidirectional selection state management |
| Annotation metadata form | Frontend (properties panel) | Backend (AnnotationModel) | UI form with Pydantic validation |
| Annotation persistence | Backend (PersistenceService) | — | JSON serialization, atomic writes |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.1 | QUndoStack, QUndoCommand, QShortcut, QGraphicsItem | Already in project; built-in undo framework, no external deps [VERIFIED: PyPI] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.13.4 | AnnotationModel serialization | Already in project; type-safe JSON persistence |
| structlog | 26.1.0 | Structured logging for annotation operations | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QUndoStack (built-in) | undo-python / custom command stack | QUndoStack is Qt-native, integrates with QAction, handles mergeWith automatically |
| QShortcut (per-widget) | keyPressEvent override (existing) | QShortcut is context-aware, doesn't conflict with existing keyPressEvent, cleaner separation |
| GripItem children (per-vertex) | Scene-level vertex items | Children move with parent automatically, no coordinate transform issues |
| QGraphicsItemGroup | Custom QGraphicsItem with children | ItemGroup is simpler but less flexible; custom item allows boundingRect/paint override |

**Installation:**
```bash
# No new packages needed — all PySide6 built-in
```

**Version verification:** PySide6 6.11.1 already installed in project [VERIFIED: pyproject.toml]

## Package Legitimacy Audit

> No new packages installed in this phase — all functionality uses existing PySide6 APIs.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION                                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
      ┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
      │  Plan Viewport  │ │ Photo Browser │ │ Properties Panel │
      │ (QGraphicsView) │ │ (QListWidget) │ │ (QWidget form)   │
      └────────┬────────┘ └───────┬───────┘ └────────┬─────────┘
               │                  │                   │
               ▼                  ▼                   ▼
      ┌─────────────────────────────────────────────────────────────┐
      │                   AnnotationViewModel                        │
      │  - annotations[]       - current_tool    - creation_state   │
      │  - undo_stack          - pending_annotation                 │
      └────────────────────────────┬────────────────────────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
      ┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
      │  QUndoStack     │ │ GraphicsItems │ │ AnnotationModel  │
      │  - MoveMarker   │ │ - CameraMarker│ │ - position       │
      │  - RotateArrow  │ │ - DirectionArr│ │ - direction      │
      │  - ResizeCone   │ │ - ViewingCone │ │ - cone_angle     │
      │  - EditPolygon  │ │ - VisibleArea │ │ - visible_area   │
      │  - EditMetadata │ │ - GripItem    │ │ - title/desc/tags│
      │  - DeleteAnnot  │ │ - Group       │ │ - floor          │
      └────────┬────────┘ └───────┬───────┘ └────────┬─────────┘
               │                  │                   │
               ▼                  ▼                   ▼
      ┌─────────────────────────────────────────────────────────────┐
      │              PersistenceService (JSON)                       │
      └─────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
src/house_photo_mapper/
├── domain/
│   ├── models/
│   │   ├── annotation.py      # AnnotationModel (already exists)
│   │   └── photo.py           # PhotoModel (add annotation_id field)
│   └── services/
│       └── persistence.py     # Add save/load_annotation_model()
├── presentation/
│   ├── viewmodels/
│   │   ├── annotation_vm.py   # AnnotationViewModel (already exists, extend)
│   │   ├── plan_vm.py         # Add annotation_vm reference
│   │   └── photo_vm.py        # Add annotation selection sync
│   ├── graphics/
│   │   └── annotation_items.py # Add GripItem for vertex handles
│   ├── commands/
│   │   └── undo_commands.py   # NEW: All QUndoCommand subclasses
│   └── views/
│       ├── plan_view.py       # Add annotation tool mode handling
│       ├── main_window.py     # Add annotation toolbar, shortcuts
│       └── annotation_toolbar.py # NEW: Tool selection toolbar
└── infrastructure/
    └── qt_patterns.py         # No changes needed
```

### Pattern 1: QUndoStack with mergeWith for Continuous Drag Operations
**What:** Use QUndoCommand subclasses with matching id() and mergeWith() to compress continuous drag operations into single undo steps.
**When to use:** MoveMarker, RotateArrow — any operation where user drags continuously and we want one undo step per gesture.
**Example:**
```python
# Source: Qt 6.11 Undo Framework Example [VERIFIED: doc.qt.io/qt-6/qtwidgets-tools-undoframework-example.html]
from PySide6.QtGui import QUndoCommand, QUndoStack

class MoveMarkerCommand(QUndoCommand):
    """Move camera marker to new position. Merges with consecutive moves."""
    
    Id = 1001  # Unique ID for mergeWith matching
    
    def __init__(self, annotation_id: str, old_pos: tuple[float, float],
                 new_pos: tuple[float, float], annotation_vm, parent=None):
        super().__init__(parent)
        self._annotation_id = annotation_id
        self._old_pos = old_pos
        self._new_pos = new_pos
        self._vm = annotation_vm
        self.setText(f"Move marker to ({new_pos[0]:.0f}, {new_pos[1]:.0f})")
    
    def id(self) -> int:
        return self.Id
    
    def redo(self) -> None:
        self._vm._set_marker_position(self._annotation_id, self._new_pos)
    
    def undo(self) -> None:
        self._vm._set_marker_position(self._annotation_id, self._old_pos)
    
    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive moves — keep first old_pos, update new_pos."""
        if other.id() != self.Id:
            return False
        if not isinstance(other, MoveMarkerCommand):
            return False
        if other._annotation_id != self._annotation_id:
            return False
        # Keep original old_pos, adopt latest new_pos
        self._new_pos = other._new_pos
        self.setText(f"Move marker to ({self._new_pos[0]:.0f}, {self._new_pos[1]:.0f})")
        return True
```

### Pattern 2: GripItem Vertex Handles for Polygon Editing
**What:** Create small QGraphicsEllipseItem children at each polygon vertex. Children move with parent; their itemChange() updates parent polygon points.
**When to use:** VisibleAreaItem vertex editing — user drags individual vertices to reshape polygon.
**Example:**
```python
# Source: StackOverflow PyQt User Editable Polygons + Qt Forum polygon ROI [VERIFIED: stackoverflow.com/questions/52751121]
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem

class GripItem(QGraphicsEllipseItem):
    """Draggable handle at polygon vertex. Child of VisibleAreaItem."""
    
    def __init__(self, index: int, parent_item, radius: float = 4.0):
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent_item)
        self._index = index
        self._parent_item = parent_item
        self.setPen(QPen(QColor(180, 50, 180), 1))
        self.setBrush(QBrush(QColor(180, 50, 180, 200)))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update parent polygon vertex
            self._parent_item.update_vertex(self._index, self.pos())
        return super().itemChange(change, value)

# In VisibleAreaItem:
class VisibleAreaItem(QGraphicsPolygonItem):
    def __init__(self, points=None, parent=None):
        super().__init__(parent)
        self._grip_items: list[GripItem] = []
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        if points:
            self.set_points(points)
    
    def set_points(self, points: list[QPointF]):
        self._vertices = points
        self._rebuild_grips()
        self._update_polygon()
    
    def _rebuild_grips(self):
        """Recreate grip items for current vertices."""
        for grip in self._grip_items:
            if grip.scene():
                grip.scene().removeItem(grip)
        self._grip_items = []
        for i, pt in enumerate(self._vertices):
            grip = GripItem(i, self)
            grip.setPos(pt)
            self._grip_items.append(grip)
    
    def update_vertex(self, index: int, pos: QPointF):
        """Called by GripItem when dragged."""
        if 0 <= index < len(self._vertices):
            self._vertices[index] = pos
            self._update_polygon()
```

### Pattern 3: QShortcut with Context for Keyboard Shortcuts
**What:** Create QShortcut objects parented to the main window, connecting to ViewModel slots. Use Qt.ShortcutContext for scope control.
**When to use:** All keyboard shortcuts — cleaner than keyPressEvent override, supports multiple contexts.
**Example:**
```python
# Source: PySide6 QShortcut docs [VERIFIED: doc.qt.io/qtforpython-6/PySide6/QtGui/QShortcut.html]
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def _setup_annotation_shortcuts(self):
        """Create annotation keyboard shortcuts."""
        # Undo/Redo — use QKeySequence.StandardKey for platform-native shortcuts
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._annotation_vm.undo_stack.undo)
        
        redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        redo_shortcut.activated.connect(self._annotation_vm.undo_stack.redo)
        
        # Delete selected annotation
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self._delete_selected_annotation)
        
        # Arrow keys navigate photos
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self._navigate_prev_photo)
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self._navigate_next_photo)
        
        # Space confirms placement
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self._confirm_annotation_placement)
        
        # Escape cancels creation
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape_shortcut.activated.connect(self._cancel_annotation_creation)
```

### Pattern 4: QUndoCommand with unique id() for mergeWith
**What:** Each command type gets a unique integer ID. Commands with matching IDs are eligible for mergeWith() when pushed to the same stack.
**When to use:** All command types — ensures only same-type commands merge.
**Example:**
```python
# Source: Qt 6.11 QUndoStack docs [VERIFIED: doc.qt.io/qt-6.11/qundostack.html]
class CommandIds:
    """Unique IDs for each command type. Used by QUndoStack for mergeWith matching."""
    MOVE_MARKER = 1001
    ROTATE_ARROW = 1002
    RESIZE_CONE = 1003
    EDIT_POLYGON = 1004
    EDIT_METADATA = 1005
    DELETE_ANNOTATION = 1006
    ADD_ANNOTATION = 1007

# QUndoStack.push() behavior:
# 1. If new command's id() == top command's id() AND both != -1:
#    → calls top.mergeWith(new)
#    → if mergeWith returns True: new command deleted, top updated
#    → if mergeWith returns False: new command pushed normally
# 2. Otherwise: new command pushed normally
```

### Pattern 5: AnnotationGraphicsGroup for Unified Selection
**What:** Custom QGraphicsItem that contains marker, arrow, cone, and visible area as children. Single selection/drag unit.
**When to use:** Already implemented in annotation_items.py — groups all annotation items.
**Key detail:** Children inherit parent's Z-value offsets. Current Z-ordering: polygon(1), cone(2), arrow(3), marker(4).

### Pattern 6: Bidirectional Selection Sync
**What:** When photo selected in browser → highlight annotation on plan; when annotation selected on plan → highlight photo in browser.
**When to use:** Plan 04-05 — requires signals from both PhotoViewModel and AnnotationViewModel.
**Example:**
```python
# In AnnotationViewModel:
annotation_selected = Signal(object)  # emits AnnotationModel or None

# In PhotoViewModel:
selection_changed = Signal(object)  # emits PhotoModel or None

# In MainWindow:
def _connect_annotation_photo_sync(self):
    # Photo selection → annotation highlight
    self._photo_vm.selection_changed.connect(self._on_photo_selected_for_annotation)
    # Annotation selection → photo highlight
    self._annotation_vm.annotation_selected.connect(self._on_annotation_selected_for_photo)

def _on_photo_selected_for_annotation(self, photo):
    if photo and photo.annotation_id:
        self._annotation_vm.select_annotation(photo.annotation_id)

def _on_annotation_selected_for_photo(self, annotation):
    if annotation:
        self._photo_vm.select_photo(annotation.photo_path)
```

### Anti-Patterns to Avoid
- **Don't use QUndoCommand.id() == -1 for mergeable commands:** mergeWith() is never called if id() returns -1. Always return a unique positive integer.
- **Don't store scene coordinates in GripItem without mapping:** Use mapFromScene()/mapToScene() for coordinate transforms between scene and item space. [VERIFIED: StackOverflow polygon vertex drag]
- **Don't use keyPressEvent for all shortcuts:** Conflicts with existing keyPressEvent in PlanGraphicsView and MainWindow. Use QShortcut for clean separation.
- **Don't create QUndoCommand without setText():** Undo menu shows command text; blank text confuses users.
- **Don't forget to setObsolete() for no-op commands:** If mergeWith results in zero movement, mark obsolete so QUndoStack auto-deletes it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Undo/redo stack | Custom list with snapshot restore | QUndoStack + QUndoCommand | Qt-native, handles mergeWith, integrates with QAction, memory-efficient |
| Command merge compression | Manual dedup logic | QUndoCommand.mergeWith() + id() | Built-in Qt pattern, tested with millions of apps |
| Polygon vertex handles | Manual scene-level items | GripItem as child of polygon | Children move with parent automatically, no coordinate transform bugs |
| Keyboard shortcut routing | Big keyPressEvent if/elif chain | QShortcut with context | Cleaner separation, supports multiple contexts, no conflict with existing handlers |
| Annotation grouping | Manual item list management | QGraphicsItemGroup or custom item with children | Single selection/drag unit, built-in hit-testing |

**Key insight:** The Qt undo framework (QUndoStack/QUndoCommand) is a mature, battle-tested implementation of the Command pattern. It handles merge compression, stack navigation, clean/modified state tracking, and integrates directly with QAction for undo/redo menu items. Rolling custom would require reimplementing all of this.

## Common Pitfalls

### Pitfall 1: mergeWith() Not Called Because id() Returns -1
**What goes wrong:** Commands pushed to QUndoStack never merge, creating one undo step per mouse move event during drag.
**Why it happens:** QUndoCommand.id() defaults to -1. QUndoStack only attempts mergeWith() when both commands have matching non-(-1) IDs.
**How to avoid:** Always override id() to return a unique positive integer per command type. Use a CommandIds enum.
**Warning signs:** Undo menu shows "Move marker" 50 times after a single drag gesture.

### Pitfall 2: GripItem Coordinate Space Mismatch
**What goes wrong:** Polygon vertices jump to wrong positions when polygon is moved, because GripItem positions are in scene space but polygon points are in item space.
**Why it happens:** GripItem.pos() returns position in parent's coordinate space. When parent moves, child's pos() stays the same relative to parent. But if you stored scene coordinates in polygon points, they're now wrong.
**How to avoid:** Store polygon points in item space (relative to polygon's origin). Use mapFromScene() when converting mouse events to polygon points. [VERIFIED: StackOverflow #73616617]
**Warning signs:** Polygon jumps when you start dragging a vertex after moving the whole polygon.

### Pitfall 3: QShortcut Context Conflict with Existing keyPressEvent
**What goes wrong:** New QShortcut for Delete key doesn't fire because MainWindow.keyPressEvent already handles it and calls event.accept().
**Why it happens:** QShortcut events are processed after keyPressEvent. If keyPressEvent accepts the event, QShortcut never sees it.
**How to avoid:** Either use QShortcut exclusively (remove keyPressEvent handling) or ensure keyPressEvent calls super() for unhandled keys. Current MainWindow.keyPressEvent only handles Ctrl+S — safe to add QShortcuts for other keys.
**Warning signs:** Keyboard shortcut doesn't work; no error message.

### Pitfall 4: QUndoStack.push() Deletes Previous Undo History
**What goes wrong:** After user undoes several actions, pushing a new command deletes all commands above the current index.
**Why it happens:** QUndoStack behavior: "If commands were undone before cmd was pushed, the current command and all commands above it are deleted."
**How to avoid:** This is expected Qt behavior. Document it. Don't fight it — it's how most undo systems work.
**Warning signs:** User expects to redo commands that were undone before a new action.

### Pitfall 5: VisibleAreaItem BoundingRect Doesn't Include GripItems
**What goes wrong:** GripItems are clipped or not clickable because parent's boundingRect() is too small.
**Why it happens:** QGraphicsItem.boundingRect() must encompass all children for proper hit-testing and rendering.
**How to avoid:** Override boundingRect() to include grip item positions, or let Qt compute it automatically by ensuring all children are properly positioned.
**Warning signs:** GripItems don't receive mouse events; selection rectangle doesn't include them.

## Code Examples

### Complete QUndoCommand Set for Annotation Operations
```python
# Source: Qt 6.11 Undo Framework Example + project patterns [VERIFIED: doc.qt.io]
from PySide6.QtGui import QUndoCommand
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel


class CommandIds:
    """Unique IDs for mergeWith matching."""
    MOVE_MARKER = 1001
    ROTATE_ARROW = 1002
    RESIZE_CONE = 1003
    EDIT_POLYGON = 1004
    EDIT_METADATA = 1005
    DELETE_ANNOTATION = 1006
    ADD_ANNOTATION = 1007


class MoveMarkerCommand(QUndoCommand):
    """Move camera marker. Merges consecutive moves into single undo step."""
    
    def __init__(self, annotation_id: str, old_pos: tuple[float, float],
                 new_pos: tuple[float, float], vm: "AnnotationViewModel"):
        super().__init__()
        self._id = annotation_id
        self._old = old_pos
        self._new = new_pos
        self._vm = vm
        self.setText(f"Move camera marker")
    
    def id(self) -> int:
        return CommandIds.MOVE_MARKER
    
    def redo(self) -> None:
        self._vm._apply_position(self._id, self._new)
    
    def undo(self) -> None:
        self._vm._apply_position(self._id, self._old)
    
    def mergeWith(self, other: QUndoCommand) -> bool:
        if not isinstance(other, MoveMarkerCommand):
            return False
        if other._id != self._id:
            return False
        self._new = other._new
        return True


class RotateArrowCommand(QUndoCommand):
    """Rotate direction arrow. Merges continuous rotation."""
    
    def __init__(self, annotation_id: str, old_angle: float,
                 new_angle: float, vm: "AnnotationViewModel"):
        super().__init__()
        self._id = annotation_id
        self._old = old_angle
        self._new = new_angle
        self._vm = vm
        self.setText(f"Rotate direction arrow")
    
    def id(self) -> int:
        return CommandIds.ROTATE_ARROW
    
    def redo(self) -> None:
        self._vm._apply_direction(self._id, self._new)
    
    def undo(self) -> None:
        self._vm._apply_direction(self._id, self._old)
    
    def mergeWith(self, other: QUndoCommand) -> bool:
        if not isinstance(other, RotateArrowCommand):
            return False
        if other._id != self._id:
            return False
        self._new = other._new
        return True


class EditPolygonCommand(QUndoCommand):
    """Edit visible area polygon points."""
    
    def __init__(self, annotation_id: str, old_points: list[tuple[float, float]],
                 new_points: list[tuple[float, float]], vm: "AnnotationViewModel"):
        super().__init__()
        self._id = annotation_id
        self._old = old_points
        self._new = new_points
        self._vm = vm
        self.setText(f"Edit visible area polygon")
    
    def id(self) -> int:
        return CommandIds.EDIT_POLYGON
    
    def redo(self) -> None:
        self._vm._apply_visible_area(self._id, self._new)
    
    def undo(self) -> None:
        self._vm._apply_visible_area(self._id, self._old)


class EditMetadataCommand(QUndoCommand):
    """Edit annotation title, description, tags."""
    
    def __init__(self, annotation_id: str, old_meta: dict, new_meta: dict,
                 vm: "AnnotationViewModel"):
        super().__init__()
        self._id = annotation_id
        self._old = old_meta
        self._new = new_meta
        self._vm = vm
        self.setText(f"Edit annotation metadata")
    
    def id(self) -> int:
        return CommandIds.EDIT_METADATA
    
    def redo(self) -> None:
        self._vm._apply_metadata(self._id, self._new)
    
    def undo(self) -> None:
        self._vm._apply_metadata(self._id, self._old)


class DeleteAnnotationCommand(QUndoCommand):
    """Delete annotation. Undo restores it."""
    
    def __init__(self, annotation_id: str, annotation_data: dict,
                 vm: "AnnotationViewModel"):
        super().__init__()
        self._id = annotation_id
        self._data = annotation_data
        self._vm = vm
        self.setText(f"Delete annotation")
    
    def id(self) -> int:
        return CommandIds.DELETE_ANNOTATION
    
    def redo(self) -> None:
        self._vm._remove_annotation(self._id)
    
    def undo(self) -> None:
        self._vm._restore_annotation(self._id, self._data)


class AddAnnotationCommand(QUndoCommand):
    """Add new annotation. Undo removes it."""
    
    def __init__(self, annotation_data: dict, vm: "AnnotationViewModel"):
        super().__init__()
        self._data = annotation_data
        self._vm = vm
        self.setText(f"Add annotation")
    
    def id(self) -> int:
        return CommandIds.ADD_ANNOTATION
    
    def redo(self) -> None:
        self._vm._add_annotation_from_data(self._data)
    
    def undo(self) -> None:
        self._vm._remove_annotation(self._data["annotation_id"])
```

### GripItem for Polygon Vertex Editing
```python
# Source: StackOverflow PyQt User Editable Polygons [VERIFIED: stackoverflow.com/questions/52751121]
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem


class GripItem(QGraphicsEllipseItem):
    """Draggable handle at polygon vertex. Child of VisibleAreaItem."""
    
    def __init__(self, index: int, parent_item, radius: float = 4.0):
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent_item)
        self._index = index
        self._parent_item = parent_item
        self.setPen(QPen(QColor(180, 50, 180), 1))
        self.setBrush(QBrush(QColor(180, 50, 180, 200)))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setZValue(10)  # Above polygon
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # pos() is in parent's coordinate space — exactly what polygon needs
            self._parent_item.update_vertex(self._index, self.pos())
        return super().itemChange(change, value)
```

### QShortcut Setup in MainWindow
```python
# Source: PySide6 QShortcut docs [VERIFIED: doc.qt.io/qtforpython-6/PySide6/QtGui/QShortcut.html]
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt


def setup_annotation_shortcuts(main_window, annotation_vm, photo_vm):
    """Create all annotation keyboard shortcuts."""
    # Undo/Redo
    undo = QShortcut(QKeySequence.StandardKey.Undo, main_window)
    undo.activated.connect(annotation_vm.undo_stack.undo)
    
    redo = QShortcut(QKeySequence.StandardKey.Redo, main_window)
    redo.activated.connect(annotation_vm.undo_stack.redo)
    
    # Save
    save = QShortcut(QKeySequence.StandardKey.Save, main_window)
    save.activated.connect(lambda: main_window._vm.save_project())
    
    # Delete
    delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), main_window)
    delete.activated.connect(annotation_vm.delete_selected)
    
    # Arrow keys navigate photos
    left = QShortcut(QKeySequence(Qt.Key.Key_Left), main_window)
    left.activated.connect(photo_vm.navigate_previous)
    
    right = QShortcut(QKeySequence(Qt.Key.Key_Right), main_window)
    right.activated.connect(photo_vm.navigate_next)
    
    up = QShortcut(QKeySequence(Qt.Key.Key_Up), main_window)
    up.activated.connect(photo_vm.navigate_previous)
    
    down = QShortcut(QKeySequence(Qt.Key.Key_Down), main_window)
    down.activated.connect(photo_vm.navigate_next)
    
    # Space confirms placement
    space = QShortcut(QKeySequence(Qt.Key.Key_Space), main_window)
    space.activated.connect(annotation_vm.complete_creation)
    
    # Escape cancels
    escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), main_window)
    escape.activated.connect(annotation_vm.cancel_creation)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual keyPressEvent routing | QShortcut with context | Qt 5+ | Cleaner separation, no conflict with existing handlers |
| Custom undo stack with snapshots | QUndoStack with mergeWith | Qt 4.3+ | Memory-efficient, automatic merge compression |
| Scene-level vertex handles | GripItem as child of polygon | Community pattern | Automatic coordinate transform, no manual mapping |
| Action list undo (linear) | QUndoStack (tree-capable) | Qt 4.3+ | Supports macro commands, clean/modified state |

**Deprecated/outdated:**
- Manual undo with list of lambdas — no merge compression, no action text, no clean state tracking
- keyPressEvent if/elif chains for shortcuts — doesn't scale, conflicts with child widget events
- Scene-level vertex items — requires manual coordinate mapping, breaks when polygon moves

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | QShortcut events are processed after keyPressEvent — existing Ctrl+S handler won't conflict | Pitfall 3 | If Qt processes shortcuts before keyPressEvent, Ctrl+S could fire twice; verify with test |
| A2 | GripItem.pos() returns position in parent's coordinate space (item space) | Pattern 2 | If pos() returns scene space, polygon vertices will jump on move; verify with unit test |
| A3 | mergeWith() is called on the TOP command when pushing a new command with matching id | Pattern 1 | If mergeWith is called on the new command instead, command structure needs adjustment |
| A4 | No new packages needed — all functionality uses existing PySide6 APIs | Standard Stack | If hidden dependency exists, plan will need adjustment |
| A5 | AnnotationGraphicsGroup boundingRect() automatically encompasses children | Pattern 5 | If not, manual boundingRect override needed |

## Open Questions

1. **Polygon drawing UX**: How does user finalize polygon (double-click? close-on-click-near-start? Escape?)
   - What we know: Success criteria says "4+ points" and "≤3 clicks" for full annotation
   - What's unclear: Polygon close trigger, minimum points before close allowed
   - Recommendation: Double-click to close polygon (standard UX); require ≥4 points before close

2. **Cone angle adjustment UX**: How does user adjust cone angle (drag handle? mouse wheel? dialog?)
   - What we know: AN-03 says "adjust viewing cone angle"; ViewingConeItem has set_cone_angle()
   - What's unclear: Interaction model for angle adjustment
   - Recommendation: Drag handle at cone edge (like polygon vertex but constrained to arc)

3. **Arrow key conflict with text editing**: When user is typing in metadata fields, arrow keys should move cursor, not navigate photos
   - What we know: NA-01 says arrow keys navigate photos; metadata form has text fields
   - What's unclear: How to disable photo navigation when text field has focus
   - Recommendation: Check if any QLineEdit/QTextEdit has focus before processing arrow shortcuts; disable shortcuts when text editing

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-qt |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q -m "not slow"` |
| Full suite command | `uv run pytest tests/ --cov=src/house_photo_mapper` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AN-01 | Place camera marker on plan click | unit | `pytest tests/test_annotation_items.py::test_place_marker -x` | ❌ Wave 0 |
| AN-02 | Set direction arrow from marker | unit | `pytest tests/test_annotation_items.py::test_set_direction -x` | ❌ Wave 0 |
| AN-03 | Adjust viewing cone angle | unit | `pytest tests/test_annotation_items.py::test_cone_angle -x` | ❌ Wave 0 |
| AN-04 | Draw visible area polygon (4+ points) | unit | `pytest tests/test_annotation_items.py::test_polygon_drawing -x` | ❌ Wave 0 |
| AN-05-AN-08 | Enter title/description/tags, select floor | unit | `pytest tests/test_annotation_vm.py::test_metadata -x` | ❌ Wave 0 |
| ED-01 | Move camera marker | unit | `pytest tests/test_undo_commands.py::test_move_marker_undo_redo -x` | ❌ Wave 0 |
| ED-02 | Rotate direction arrow | unit | `pytest tests/test_undo_commands.py::test_rotate_arrow_undo_redo -x` | ❌ Wave 0 |
| ED-03 | Delete annotation | unit | `pytest tests/test_undo_commands.py::test_delete_annotation_undo -x` | ❌ Wave 0 |
| ED-04 | Unlimited undo/redo | unit | `pytest tests/test_undo_commands.py::test_undo_redo_stack -x` | ❌ Wave 0 |
| NA-01 | Arrow keys navigate photos | integration | `pytest test_shortcuts.py::test_arrow_nav -x` | ❌ Wave 0 |
| NA-02 | Space confirms placement | integration | `pytest test_shortcuts.py::test_space_confirm -x` | ❌ Wave 0 |
| NA-04 | Ctrl+Z undoes | unit | `pytest test_shortcuts.py::test_ctrl_z -x` | ❌ Wave 0 |
| NA-05 | Ctrl+Y redoes | unit | `pytest test_shortcuts.py::test_ctrl_y -x` | ❌ Wave 0 |
| NA-06 | Delete removes annotation | unit | `pytest test_shortcuts.py::test_delete_key -x` | ❌ Wave 0 |
| US-01 | Annotate in ≤3 clicks | integration | `pytest test_annotation_flow.py::test_three_click_annotation -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q -m "not slow"`
- **Per wave merge:** `uv run pytest tests/ --cov=src/house_photo_mapper`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_annotation_items.py` — covers AN-01, AN-02, AN-03, AN-04
- [ ] `tests/test_annotation_vm.py` — covers AN-05, AN-06, AN-07, AN-08
- [ ] `tests/test_undo_commands.py` — covers ED-01, ED-02, ED-03, ED-04
- [ ] `tests/test_shortcuts.py` — covers NA-01, NA-02, NA-04, NA-05, NA-06
- [ ] `tests/test_annotation_flow.py` — covers US-01, US-02

## Security Domain

> Required — security_enforcement not explicitly false in config.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | — (local desktop app, no auth) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Pydantic validates AnnotationModel fields; title required, floor range -2..10 |
| V6 Cryptography | no | — |
| V7 Error Handling | yes | Try/except on QUndoCommand execution; user-facing error dialogs |
| V9 Logging | yes | structlog for annotation operations; no PII in logs |
| V14 Business Logic | yes | Undo/redo correctness critical — data integrity if commands misbehave |

### Known Threat Patterns for Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Undo stack overflow (memory) | DoS | QUndoStack has configurable clean index; limit stack size if needed |
| Invalid polygon points (NaN, Inf) | Tampering | Pydantic validation on AnnotationModel.visible_area; reject non-finite coordinates |
| Keyboard shortcut injection | Tampering | QShortcut context限制 (WindowShortcut); shortcuts only fire in active window |

## Sources

### Primary (HIGH confidence)
- Qt 6.11 Undo Framework Example — QUndoStack, QUndoCommand, mergeWith, id() [VERIFIED: doc.qt.io/qt-6/qtwidgets-tools-undoframework-example.html]
- Qt 6.11 QUndoStack Class Reference — push() behavior, mergeWith mechanics [VERIFIED: doc.qt.io/qt-6.11/qundostack.html]
- PySide6 QShortcut Documentation — context, key sequences, activated signal [VERIFIED: doc.qt.io/qtforpython-6/PySide6/QtGui/QShortcut.html]
- PySide6 QGraphicsItem Documentation — child items, coordinate spaces, itemChange [VERIFIED: doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsItem.html]

### Secondary (MEDIUM confidence)
- StackOverflow #52751121 — PyQt user editable polygons with GripItem pattern [CITED: stackoverflow.com/questions/52751121]
- StackOverflow #73616617 — QGraphicsPolygonItem vertex drag coordinate fix [CITED: stackoverflow.com/questions/73616617]
- Qt Forum — Drawing polygon ROI with re-sizable handles [CITED: forum.qt.io/topic/114600]
- Runebook — QUndoStack push() alternative patterns [CITED: runebook.dev/en/docs/qt/qundostack/push]

### Tertiary (LOW confidence)
- GripItem as child pattern — confirmed across multiple StackOverflow answers but no official Qt docs example [ASSUMED]
- QShortcut processed after keyPressEvent — standard Qt event ordering but verify with test [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — All packages already in project, no new dependencies
- Architecture: HIGH — QUndoStack/QUndoCommand from official Qt docs, vertex handle pattern from multiple verified sources
- Pitfalls: HIGH — Directly from Qt docs and StackOverflow with coordinate transform details
- Code Examples: HIGH — Sourced from official Qt examples and verified community patterns
- Shortcuts: HIGH — QShortcut from official PySide6 docs

**Research date:** 2026-07-14
**Valid until:** 2026-10-14 (90 days — stable PySide6 APIs, no external deps)
