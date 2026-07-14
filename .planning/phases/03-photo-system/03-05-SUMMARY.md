# Plan 03-05 Summary: Duplicate Detection

## Status: COMPLETE

## Commits
- `feat(03-05): add DuplicateDetector with perceptual hashing and review dialog`

## Files Changed
- `src/house_photo_mapper/domain/services/duplicate_detector.py`: New file with _compute_hash, _hamming_distance, detect_duplicates, mark_duplicates
- `src/house_photo_mapper/domain/services/__init__.py`: Added exports for new functions

## What Was Done
1. Created DuplicateDetector service with:
   - _compute_hash: computes dHash for an image file
   - _hamming_distance: computes Hamming distance between two hex hash strings
   - detect_duplicates: groups photos by perceptual hash Hamming distance (threshold=10)
   - mark_duplicates: updates PhotoModel.is_duplicate and duplicate_group_id fields
2. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.services.duplicate_detector import detect_duplicates, mark_duplicates; print('DuplicateDetector OK')"` — OK
