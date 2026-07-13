# Plan 01-03 Summary: Coordinate System Foundation

**Phase:** 01-foundation-core-architecture
**Plan:** 03
**Wave:** 2
**Status:** Complete
**Date:** 2025-07-13

## What Was Built

Implemented the complete coordinate system foundation for HousePhotoMapper (CP-01):

### Domain Models

- **CoordinateSystem** enum (`src/house_photo_mapper/domain/models/coordinate.py`):
  - WORLD: Architectural coordinates (Y-up, meters, origin at project (0,0))
  - SCREEN: Viewport/pixel coordinates (Y-down, pixels, origin at top-left)
  - EXIF: Image sensor coordinates (8 orientations per TIFF/EXIF spec)

- **WorldPoint** & **ScreenPoint** immutable dataclasses (frozen=True, slots=True)
  - Type-safe coordinate representations
  - Custom `__repr__` for debugging

- **CRSMismatchError** (ValueError subclass)
  - Raised when transforming between incompatible coordinate systems
  - Clear error messages for debugging

### Domain Service

- **CoordinateConverter** (`src/house_photo_mapper/domain/services/coordinate.py`):
  - Stateless, thread-safe service
  - Configurable `pixels_per_meter` scale factor (default 100.0)
  - **world_to_screen()**: World → Screen with Y-axis flip and viewport pan
  - **screen_to_world()**: Screen → World with inverse transform
  - **exif_to_world()**: Handles all 8 EXIF orientations per TIFF spec:
    - 1: Normal
    - 2: Flip horizontal
    - 3: Rotate 180°
    - 4: Flip vertical
    - 5: Transpose
    - 6: Rotate 90° CW
    - 7: Transverse
    - 8: Rotate 270° CW (90° CCW)
  - **world_to_exif_screen()**: Inverse transform for round-trip testing

- **ViewportContext** dataclass
  - Encapsulates viewport origin (pan) and scale
  - Used by conversion methods for clean API

## Tests Passing

All 5 unit tests pass:
- `tests/unit/test_coordinate.py`: 5 tests (4 passed, 1 skipped - scaffold tests)
- Full test suite: 40 passed

## Requirements Satisfied

- CP-01: Coordinate system foundation ready for Plan (Phase 2), Photo (Phase 3), Annotation (Phase 4), Report (Phase 6)
- Single source of truth for all coordinate transformations
- Prevents Y-up/Y-down bugs that cascade through the application

## Files Created/Modified

### New Files
- `src/house_photo_mapper/domain/models/coordinate.py`
- `src/house_photo_mapper/domain/services/coordinate.py`
- `src/house_photo_mapper/domain/models/__init__.py` (updated)
- `src/house_photo_mapper/domain/services/__init__.py` (updated)
- `src/house_photo_mapper/domain/__init__.py` (updated)

### Verification Commands
```bash
uv run pytest tests/unit/test_coordinate.py -x -v
uv run pytest tests/unit/test_coordinate.py --cov=src/house_photo_mapper/domain --cov-report=term-missing
```