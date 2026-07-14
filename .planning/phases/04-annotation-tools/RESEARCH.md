# Phase 4: Annotation Tools - Research

## Goal
User can place a camera marker on the plan, set direction and viewing cone, draw a visible-area polygon (4+ points), enter title/description/tags, assign a floor, and edit everything with unlimited undo/redo using professional keyboard shortcuts.

## Current Architecture

### Domain Models
- `ProjectModel` has `annotations: list[dict[str, Any]]` field (unused)
- `PlanModel` has `pages: List[PageModel]` with floor assignment
- `PhotoModel` has no annotation binding yet
- `CalibrationModel` stores pixels_per_meter for real-world conversion

### ViewModels
- `PlanViewModel` manages plan pages, zoom, rotation
- `ProjectViewModel` orchestrates project CRUD
- `PhotoViewModel` manages photo collection and selection

### Views
- `PlanView` uses `PlanGraphicsScene` (NoIndex mode) and `PlanGraphicsView`
- `PlanGraphicsView` handles zoom/pan/rotate
- `MainWindow` has disabled Undo/Redo actions

### Infrastructure
- No QUndoStack exists yet
- No annotation graphics items exist yet

## Key Integration Points

1. **PlanView.set_scene_pixmap()** calls `self._scene.clear()` which destroys annotation items
2. **PlanGraphicsView** needs tool mode handling for annotation placement
3. **MainWindow** needs annotation toolbar, properties panel, keyboard shortcuts
4. **PhotoViewModel.select_photo()** emits `selection_changed` - hook for annotation workflow
5. **ProjectViewModel.save_project()** needs annotation persistence

## Files to Create
- `domain/models/annotation.py` - AnnotationModel
- `presentation/viewmodels/annotation_vm.py` - AnnotationViewModel
- `presentation/graphics/annotation_items.py` - QGraphicsItem subclasses
- `presentation/commands/undo_commands.py` - QUndoCommand subclasses

## Files to Modify
- `domain/models/photo.py` - add `annotation_id: Optional[str]`
- `domain/services/persistence.py` - add annotation save/load
- `presentation/views/plan_view.py` - fix clear() to preserve annotations
- `presentation/views/main_window.py` - add annotation UI
- `presentation/viewmodels/plan_vm.py` - add annotation signals
- `presentation/viewmodels/project_vm.py` - add annotation persistence

## Patterns to Follow
- Pydantic BaseModel for domain models
- `to_project_json()` / `from_project_json()` serialization
- QtSafeViewModel base class
- Signal-based UI sync
- Atomic write pattern in PersistenceService
- Z-ordering: plan (0), polygon (1), cone (2), arrow (3), marker (4)
