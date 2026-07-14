# Plan 03-02 Summary: Photo Import Pipeline

## Status: COMPLETE

## Commits
- `feat(03-02): add PhotoImporter service with drag-drop and recursive folder scan`

## Files Changed
- `src/house_photo_mapper/domain/services/photo_importer.py`: New file with SUPPORTED_FORMATS, scan_folder_recursive, import_single_photo, import_photos
- `src/house_photo_mapper/domain/services/__init__.py`: Added exports for new functions
- `src/house_photo_mapper/presentation/viewmodels/main_window_vm.py`: Added import_photos and import_photos_from_folder slots
- `src/house_photo_mapper/presentation/views/main_window.py`: Added drag-drop support (setAcceptDrops, dragEnterEvent, dropEvent) and Import Photos menu action

## What Was Done
1. Created PhotoImporter service with:
   - SUPPORTED_FORMATS: jpg, jpeg, png, heic, heif, tiff, tif, bmp
   - scan_folder_recursive: recursively scans folder for images, skips hidden dirs
   - import_single_photo: opens with Pillow, applies EXIF orientation, extracts dimensions, computes perceptual hash
   - import_photos: batch import, skips duplicates by path
2. Added drag-drop support to MainWindow:
   - setAcceptDrops(True) in _setup_ui
   - dragEnterEvent: accepts if any URL has supported image extension
   - dropEvent: extracts paths and calls import_photos
3. Added Import Photos menu action with Ctrl+Shift+P shortcut
4. Added import_photos and import_photos_from_folder slots to MainWindowViewModel
5. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.services.photo_importer import scan_folder_recursive; from pathlib import Path; print(list(scan_folder_recursive(Path('.')))[:3])"` — returns list
