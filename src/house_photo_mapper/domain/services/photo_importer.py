"""Photo import service for drag-drop and folder scan import."""

from pathlib import Path
from typing import Iterator

import imagehash
from PIL import Image, ImageOps

from house_photo_mapper.domain.models.photo import ExifModel, PhotoModel


SUPPORTED_FORMATS: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".heif",
    ".tiff",
    ".tif",
    ".bmp",
}


def scan_folder_recursive(folder: Path) -> Iterator[Path]:
    """Recursively scan folder for supported image files.

    Args:
        folder: Root folder to scan.

    Yields:
        Paths to supported image files, skipping hidden directories.
    """
    for item in sorted(folder.rglob("*")):
        if item.is_dir() and item.name.startswith("."):
            continue
        if item.is_file() and item.suffix.lower() in SUPPORTED_FORMATS:
            yield item


def _extract_exif(image: Image.Image) -> ExifModel:
    """Extract EXIF metadata from PIL Image.

    Args:
        image: PIL Image with EXIF data.

    Returns:
        ExifModel with extracted metadata.
    """
    exif_data = image.getexif()
    if not exif_data:
        return ExifModel()

    from PIL import ExifTags

    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}

    # Extract GPS data
    gps_lat = None
    gps_lon = None
    gps_info = tags.get("GPSInfo")
    if gps_info:
        from PIL.ExifTags import GPSTAGS

        gps_tags = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        if "GPSLatitude" in gps_tags and "GPSLongitude" in gps_tags:
            lat = gps_tags["GPSLatitude"]
            lon = gps_tags["GPSLongitude"]
            lat_ref = gps_tags.get("GPSLatitudeRef", "N")
            lon_ref = gps_tags.get("GPSLongitudeRef", "E")

            # Convert to decimal degrees
            lat_decimal = float(lat[0]) + float(lat[1]) / 60 + float(lat[2]) / 3600
            lon_decimal = float(lon[0]) + float(lon[1]) / 60 + float(lon[2]) / 3600

            if lat_ref == "S":
                lat_decimal = -lat_decimal
            if lon_ref == "W":
                lon_decimal = -lon_decimal

            gps_lat = lat_decimal
            gps_lon = lon_decimal

    # Extract timestamp
    timestamp = None
    datetime_str = tags.get("DateTimeOriginal") or tags.get("DateTime")
    if datetime_str:
        from datetime import datetime

        try:
            timestamp = datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError):
            pass

    return ExifModel(
        timestamp=timestamp,
        camera_make=tags.get("Make"),
        camera_model=tags.get("Model"),
        lens_model=tags.get("LensModel"),
        orientation=exif_data.get(274, 1),  # 274 = Orientation tag
        gps_lat=gps_lat,
        gps_lon=gps_lon,
    )


def import_single_photo(path: Path, project_dir: Path) -> PhotoModel:
    """Import a single photo file.

    Args:
        path: Path to source photo.
        project_dir: Project directory for computing relative path.

    Returns:
        PhotoModel with metadata and perceptual hash.

    Raises:
        FileNotFoundError: If source file doesn't exist.
        ValueError: If file format not supported.
    """
    if not path.exists():
        raise FileNotFoundError(f"Photo not found: {path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {path.suffix}")

    # Open and process image
    with Image.open(path) as img:
        # Apply EXIF orientation
        img = ImageOps.exif_transpose(img)

        width, height = img.size

        # Compute perceptual hash
        phash = str(imagehash.dhash(img))

        # Extract EXIF
        exif = _extract_exif(img)

    # Compute relative path
    try:
        rel_path = str(path.relative_to(project_dir))
    except ValueError:
        rel_path = path.name

    return PhotoModel(
        path=rel_path,
        filename=path.name,
        file_size=path.stat().st_size,
        width=width,
        height=height,
        exif=exif,
        perceptual_hash=phash,
    )


def import_photos(paths: list[Path], project_dir: Path) -> list[PhotoModel]:
    """Import multiple photos, skipping duplicates by path.

    Args:
        paths: List of photo paths to import.
        project_dir: Project directory for computing relative paths.

    Returns:
        List of successfully imported PhotoModels.
    """
    seen_paths: set[str] = set()
    results: list[PhotoModel] = []

    for path in paths:
        try:
            photo = import_single_photo(path, project_dir)
            if photo.path not in seen_paths:
                seen_paths.add(photo.path)
                results.append(photo)
        except (FileNotFoundError, ValueError):
            continue

    return results
