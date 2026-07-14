"""Photo import service for drag-drop and folder scan import."""

from pathlib import Path
from typing import Iterator

import imagehash
from PIL import Image, ImageOps

from house_photo_mapper.domain.models.photo import PhotoModel
from house_photo_mapper.domain.services.exif_extractor import extract_exif


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

    # Extract EXIF using dedicated service
    exif = extract_exif(path)

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
