# Plan 03-04 Summary: Thumbnail System

## Status: COMPLETE

## Commits
- `feat(03-04): add ThumbnailGenerator with background workers, LRU memory and disk cache`

## Files Changed
- `src/house_photo_mapper/domain/services/thumbnail_generator.py`: New file with ThumbnailSignals, ThumbnailWorker, ThumbnailGenerator
- `src/house_photo_mapper/domain/services/__init__.py`: Added exports for new classes

## What Was Done
1. Created ThumbnailGenerator service with:
   - ThumbnailSignals: thumbnail_ready, thumbnail_error signals
   - ThumbnailWorker(QRunnable): generates single thumbnail in background thread
     - Opens image with Pillow, applies EXIF orientation
     - Resizes to target size (default 200x200) using LANCZOS resampling
     - Converts to QPixmap via QImage buffer
   - ThumbnailGenerator(QObject): manages background generation
     - generate(): queues thumbnail generation
     - thumbnail_ready signal: emitted when thumbnail available
     - LRU memory cache (default 100MB)
     - Disk cache in .cache/thumbnails/
     - Cache invalidation based on source file mtime
2. All 218 tests pass

## Verification
- `uv run pytest tests/ -x` — 218 passed
- `uv run python -c "from house_photo_mapper.domain.services.thumbnail_generator import ThumbnailGenerator, ThumbnailWorker; print('ThumbnailGenerator OK')"` — OK
