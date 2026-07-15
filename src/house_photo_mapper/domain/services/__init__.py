"""Domain services package."""

from house_photo_mapper.domain.services.coordinate import CoordinateConverter, ViewportContext
from house_photo_mapper.domain.services.duplicate_detector import detect_duplicates, mark_duplicates
from house_photo_mapper.domain.services.exif_extractor import extract_exif, get_exif_summary
from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.domain.services.photo_importer import (
    import_photos,
    import_single_photo,
    scan_folder_recursive,
)
from house_photo_mapper.domain.services.plan_renderer import PlanRenderer
from house_photo_mapper.domain.services.streaming_serializer import (
    estimate_file_size,
    read_photos_streaming,
    serialize_large_arrays,
)
from house_photo_mapper.domain.services.thumbnail_generator import ThumbnailGenerator, ThumbnailWorker
from house_photo_mapper.domain.services.tile_pyramid import TilePyramid, TileSpec

__all__ = [
    "PersistenceService",
    "CoordinateConverter",
    "ViewportContext",
    "PlanRenderer",
    "TilePyramid",
    "TileSpec",
    "scan_folder_recursive",
    "import_single_photo",
    "import_photos",
    "extract_exif",
    "get_exif_summary",
    "ThumbnailGenerator",
    "ThumbnailWorker",
    "detect_duplicates",
    "mark_duplicates",
    "serialize_large_arrays",
    "read_photos_streaming",
    "estimate_file_size",
]
