# Plan 03-01 Summary: Photo Models & Dependencies

## Status: COMPLETE

## Commits
- `feat(03-01): add PhotoModel, ExifModel, DuplicateGroup and install imagehash/pillow-heif`

## Files Changed
- `pyproject.toml`: Added imagehash>=4.3.2 and pillow-heif>=1.4.0 dependencies
- `src/house_photo_mapper/domain/models/photo.py`: New file with ExifModel, DuplicateGroup, PhotoModel
- `src/house_photo_mapper/domain/models/__init__.py`: Added exports for new models
- `src/house_photo_mapper/app.py`: Added _register_image_plugins() for HEIC support

## What Was Done
1. Installed imagehash and pillow-heif dependencies via uv sync
2. Created domain models following PlanModel pattern:
   - ExifModel: timestamp, camera_make, camera_model, lens_model, orientation, gps_lat, gps_lon
   - DuplicateGroup: group_id, photo_paths, representative_index
   - PhotoModel: path, filename, file_size, width, height, exif, perceptual_hash, is_duplicate, duplicate_group_id, imported_at
3. Added to_project_json() and from_project_json() class methods to PhotoModel
4. Registered pillow-heif plugin at app startup with graceful fallback
5. All 218 existing tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.models.photo import PhotoModel, ExifModel, DuplicateGroup; print('Models OK')"` — OK
- `uv run python -c "from pillow_heif import register_heif_opener; register_heif_opener(); print('HEIC OK')"` — OK
