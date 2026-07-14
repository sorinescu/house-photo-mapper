# Plan 03-03 Summary: EXIF Extraction Service

## Status: COMPLETE

## Commits
- `feat(03-03): add ExifExtractor with GPS rational conversion and orientation handling`

## Files Changed
- `src/house_photo_mapper/domain/services/exif_extractor.py`: New file with extract_exif, _gps_to_decimal, get_exif_summary
- `src/house_photo_mapper/domain/services/photo_importer.py`: Refactored to use ExifExtractor service
- `src/house_photo_mapper/domain/services/__init__.py`: Added exports for new functions
- `src/house_photo_mapper/domain/models/photo.py`: Added display_metadata() property to PhotoModel

## What Was Done
1. Created ExifExtractor service with:
   - extract_exif: opens image with Pillow, extracts DateTimeOriginal, Make, Model, LensModel, Orientation, GPS IFD
   - _gps_to_decimal: converts EXIF rational GPS to decimal degrees
   - get_exif_summary: human-readable summary for status bar display
2. Refactored PhotoImporter to use ExifExtractor service
3. Added display_metadata() property to PhotoModel for UI display
4. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.services.exif_extractor import extract_exif; print('ExifExtractor OK')"` — OK
