"""Duplicate photo detection service using perceptual hashing."""

from itertools import combinations

import imagehash
from PIL import Image

from house_photo_mapper.domain.models.photo import DuplicateGroup, PhotoModel


def _compute_hash(path: str) -> str:
    """Compute perceptual hash for an image file.

    Args:
        path: Path to image file.

    Returns:
        Hex string of perceptual hash.
    """
    try:
        with Image.open(path) as img:
            return str(imagehash.dhash(img))
    except Exception:
        return ""


def _hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hex hash strings.

    Args:
        hash1: First hash string.
        hash2: Second hash string.

    Returns:
        Number of differing bits.
    """
    if not hash1 or not hash2:
        return float("inf")  # type: ignore[return-value]

    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return h1 - h2


def detect_duplicates(
    photos: list[PhotoModel],
    project_dir: str | None = None,
    threshold: int = 10,
) -> list[DuplicateGroup]:
    """Detect duplicate photos via perceptual hashing.

    Args:
        photos: List of PhotoModel instances to check.
        project_dir: Project directory for computing full paths.
        threshold: Maximum Hamming distance to consider photos as duplicates.
            Default 10 (96% similar).

    Returns:
        List of DuplicateGroup instances grouping duplicate photos.
    """
    # Ensure all photos have perceptual hashes
    for photo in photos:
        if not photo.perceptual_hash and project_dir:
            from pathlib import Path

            full_path = Path(project_dir) / photo.path
            photo.perceptual_hash = _compute_hash(str(full_path))

    # Build groups of duplicates
    groups: list[DuplicateGroup] = []
    assigned: set[str] = set()

    for i, photo1 in enumerate(photos):
        if photo1.path in assigned or not photo1.perceptual_hash:
            continue

        group_paths = [photo1.path]

        for j, photo2 in enumerate(photos):
            if i >= j or photo2.path in assigned or not photo2.perceptual_hash:
                continue

            distance = _hamming_distance(photo1.perceptual_hash, photo2.perceptual_hash)
            if distance <= threshold:
                group_paths.append(photo2.path)

        # Only create group if we found duplicates
        if len(group_paths) > 1:
            group_id = f"dup_{i}"
            group = DuplicateGroup(
                group_id=group_id,
                photo_paths=group_paths,
                representative_index=0,
            )
            groups.append(group)

            # Mark all photos in group as assigned
            for path in group_paths:
                assigned.add(path)

    return groups


def mark_duplicates(
    photos: list[PhotoModel],
    groups: list[DuplicateGroup],
) -> None:
    """Mark photos with duplicate information.

    Args:
        photos: List of PhotoModel instances to update.
        groups: List of DuplicateGroup instances from detection.
    """
    # Build lookup from path to group
    path_to_group: dict[str, DuplicateGroup] = {}
    for group in groups:
        for path in group.photo_paths:
            path_to_group[path] = group

    # Mark photos
    for photo in photos:
        if photo.path in path_to_group:
            group = path_to_group[photo.path]
            photo.is_duplicate = True
            photo.duplicate_group_id = group.group_id
        else:
            photo.is_duplicate = False
            photo.duplicate_group_id = None
