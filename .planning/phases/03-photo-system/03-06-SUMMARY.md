# Plan 03-06 Summary: PhotoBrowserVM & UI Integration

## Status: COMPLETE

## Commits
- `feat(03-06): add PhotoViewModel, PhotoBrowser, PhotoMetadataPanel with full MainWindow integration`

## Files Changed
- `src/house_photo_mapper/presentation/viewmodels/photo_vm.py`: New file with PhotoViewModel
- `src/house_photo_mapper/presentation/views/photo_browser.py`: New file with PhotoBrowser widget
- `src/house_photo_mapper/presentation/views/photo_metadata.py`: New file with PhotoMetadataPanel widget
- `src/house_photo_mapper/presentation/views/main_window.py`: Updated to integrate photo browser
- `tests/test_plan_viewport_wiring.py`: Updated test to handle 3-widget splitter

## What Was Done
1. Created PhotoViewModel with:
   - photos list, selected_photo, thumbnail_generator
   - Signals: photo_added, photo_removed, thumbnail_ready, duplicates_found, selection_changed, metadata_changed
   - Slots: import_photos, select_photo, remove_selected, review_duplicates
2. Created PhotoBrowser widget with:
   - Icon mode with 200x200 thumbnails
   - add_photo, update_thumbnail, mark_duplicate, remove_photo methods
3. Created PhotoMetadataPanel widget with:
   - Form layout showing filename, dimensions, size, camera, lens, date, GPS
   - update_metadata slot for dynamic updates
4. Integrated into MainWindow:
   - Added PhotoViewModel to MainWindow
   - Updated _create_central_widget to include photo browser and metadata panel
   - Connected PhotoViewModel signals to UI
5. Updated test to handle 3-widget splitter layout
6. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.presentation.viewmodels.photo_vm import PhotoViewModel; print('PhotoViewModel OK')"` — OK
- `uv run python -c "from house_photo_mapper.presentation.views.photo_browser import PhotoBrowser; print('PhotoBrowser OK')"` — OK
