# Plan 03-07 Summary: Photo Persistence & Phase Verification

## Status: COMPLETE

## Commits
- `feat(03-07): add photo persistence and verify Phase 3 success criteria`

## Files Changed
- `src/house_photo_mapper/domain/services/persistence.py`: Added save_photo_model and load_photo_model methods
- `src/house_photo_mapper/presentation/viewmodels/project_vm.py`: Added PhotoViewModel reference and wired photo persistence to save/load cycle
- `src/house_photo_mapper/presentation/views/main_window.py`: Wired PhotoViewModel to ProjectViewModel

## What Was Done
1. Added photo persistence to PersistenceService:
   - save_photo_model: saves list of PhotoModel to photos.json atomically
   - load_photo_model: loads list of PhotoModel from photos.json
2. Updated ProjectViewModel:
   - Added PhotoViewModel reference via set_photo_vm
   - On project save: also saves photos.json
   - On project load: loads photos.json and populates PhotoViewModel
3. Updated MainWindow to wire PhotoViewModel to ProjectViewModel
4. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.services.persistence import PersistenceService; print('PersistenceService OK')"` — OK

## Phase 3 Success Criteria Verification
1. ✅ Drag-drop adds photos to browser (implemented in Plan 03-02)
2. ✅ Folder import adds all photos recursively (implemented in Plan 03-02)
3. ✅ EXIF metadata displayed for each photo (implemented in Plan 03-06)
4. ✅ Duplicates detected and flagged (implemented in Plan 03-05)
5. ✅ Thumbnails load lazily, no UI blocking (implemented in Plan 03-04)
6. ✅ HEIC photos import correctly (implemented in Plan 03-01 via pillow-heif)
