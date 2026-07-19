"""EXIF metadata extraction service."""

from datetime import datetime
from pathlib import Path

from PIL import Image

from house_photo_mapper.domain.models.photo import ExifModel


def _gps_to_decimal(gps_coord: tuple, gps_ref: str) -> float:
    """Convert EXIF GPS rational coordinates to decimal degrees.

    Args:
        gps_coord: Tuple of (degrees, minutes, seconds) as rational values.
        gps_ref: Reference direction (N/S for latitude, E/W for longitude).

    Returns:
        Decimal degrees (negative for S/W).
    """
    degrees = float(gps_coord[0])
    minutes = float(gps_coord[1])
    seconds = float(gps_coord[2])

    decimal = degrees + minutes / 60 + seconds / 3600

    if gps_ref in ("S", "W"):
        decimal = -decimal

    return decimal


def extract_exif(path: Path) -> ExifModel:
    """Extract EXIF metadata from an image file.

    Args:
        path: Path to image file.

    Returns:
        ExifModel with extracted metadata (defaults for missing fields).
    """
    try:
        with Image.open(path) as img:
            exif_data = img.getexif()
    except Exception:
        return ExifModel()

    if not exif_data:
        return ExifModel()

    from PIL import ExifTags

    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}

    # Extract GPS data
    gps_lat = None
    gps_lon = None
    gps_info = tags.get("GPSInfo")
    if gps_info and isinstance(gps_info, dict):
        from PIL.ExifTags import GPSTAGS

        gps_tags = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        if "GPSLatitude" in gps_tags and "GPSLongitude" in gps_tags:
            gps_lat = _gps_to_decimal(
                gps_tags["GPSLatitude"],
                gps_tags.get("GPSLatitudeRef", "N"),
            )
            gps_lon = _gps_to_decimal(
                gps_tags["GPSLongitude"],
                gps_tags.get("GPSLongitudeRef", "E"),
            )

    # Extract timestamp
    timestamp = None
    datetime_str = tags.get("DateTimeOriginal") or tags.get("DateTime")
    if datetime_str:
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


def get_exif_summary(exif: ExifModel) -> str:
    """Get a human-readable summary of EXIF metadata.

    Args:
        exif: ExifModel to summarize.

    Returns:
        Summary string for status bar display.
    """
    parts = []

    if exif.camera_make and exif.camera_model:
        parts.append(f"{exif.camera_make} {exif.camera_model}")
    elif exif.camera_make:
        parts.append(exif.camera_make)

    if exif.lens_model:
        parts.append(exif.lens_model)

    if exif.timestamp:
        parts.append(exif.timestamp.strftime("%Y-%m-%d %H:%M"))

    if exif.gps_lat is not None and exif.gps_lon is not None:
        parts.append("GPS")

    return " | ".join(parts) if parts else "No EXIF data"
