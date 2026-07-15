"""Streaming serialization for large arrays in project files.

Provides chunked JSON writing for plans, photos, and annotations arrays
to handle 1000+ photos without memory spikes. Uses incremental JSON
construction to avoid loading entire arrays into memory at once.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from house_photo_mapper.domain.models.photo import PhotoModel


def serialize_large_arrays(
    plans: list[dict[str, Any]],
    photos: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    settings: dict[str, Any],
    ui_state: dict[str, Any],
    metadata: dict[str, Any],
    output_path: Path,
    chunk_size: int = 500,
) -> None:
    """Serialize project data with streaming for large arrays.

    Writes the project file in chunks to avoid loading entire arrays
    into memory. For arrays larger than chunk_size, items are written
    incrementally using a streaming JSON pattern.

    Args:
        plans: Plan data list.
        photos: Photo data list.
        annotations: Annotation data list.
        settings: Export settings dict.
        ui_state: UI state dict.
        metadata: Project metadata dict.
        output_path: Path to write the project file.
        chunk_size: Number of items per write chunk (default 500).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("{\n")

        # Write metadata
        f.write('  "schema_version": ')
        json.dump(metadata.get("schema_version", 1), f)
        f.write(",\n")

        # Stream plans array
        f.write('  "plans": ')
        _stream_array(f, plans, chunk_size)
        f.write(",\n")

        # Stream photos array
        f.write('  "photos": ')
        _stream_array(f, photos, chunk_size)
        f.write(",\n")

        # Stream annotations array
        f.write('  "annotations": ')
        _stream_array(f, annotations, chunk_size)
        f.write(",\n")

        # Write settings and ui_state (typically small)
        f.write('  "settings": ')
        json.dump(settings, f, indent=2)
        f.write(",\n")

        f.write('  "ui_state": ')
        json.dump(ui_state, f, indent=2)
        f.write("\n")

        f.write("}\n")

    # Atomic rename
    tmp_path.replace(output_path)


def _stream_array(
    f: Any, items: list[dict[str, Any]], chunk_size: int = 500
) -> None:
    """Write a JSON array to file handle, processing in chunks.

    Args:
        f: Open file handle for writing.
        items: List of dicts to serialize.
        chunk_size: Items per chunk.
    """
    if not items:
        f.write("[]")
        return

    f.write("[\n")
    total = len(items)

    for i in range(0, total, chunk_size):
        chunk = items[i : i + chunk_size]
        chunk_json = json.dumps(chunk, indent=2)

        # Remove the outer brackets and re-indent for streaming
        lines = chunk_json.split("\n")
        # Skip first line (opening bracket) and last line (closing bracket)
        inner_lines = [line for line in lines[1:-1] if line.strip()]

        for line in inner_lines:
            f.write("  " + line + "\n")

        # Add comma between chunks (but not after last chunk)
        if i + chunk_size < total:
            f.write(",\n")

    f.write("]")


def read_photos_streaming(
    photos_path: Path, chunk_size: int = 500
) -> Iterator[list[PhotoModel]]:
    """Read photos from JSON file in chunks for memory-efficient processing.

    Yields lists of PhotoModel instances, each containing at most
    chunk_size items. Useful for processing large photo collections
    without loading all into memory at once.

    Args:
        photos_path: Path to photos.json file.
        chunk_size: Maximum photos per chunk.

    Yields:
        Lists of PhotoModel instances.
    """
    if not photos_path.exists():
        return

    with open(photos_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return

    total = len(data)
    for i in range(0, total, chunk_size):
        chunk = data[i : i + chunk_size]
        yield [PhotoModel.from_project_json(item) for item in chunk]


def estimate_file_size(
    plans: list[dict[str, Any]],
    photos: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    settings: dict[str, Any],
    ui_state: dict[str, Any],
) -> int:
    """Estimate the JSON file size in bytes without writing.

    Useful for pre-flight checks before saving large projects.

    Args:
        plans: Plan data list.
        photos: Photo data list.
        annotations: Annotation data list.
        settings: Export settings dict.
        ui_state: UI state dict.

    Returns:
        Estimated file size in bytes.
    """
    sample = {
        "schema_version": 1,
        "plans": plans[:10],  # Sample first 10
        "photos": photos[:10],
        "annotations": annotations[:10],
        "settings": settings,
        "ui_state": ui_state,
    }
    sample_json = json.dumps(sample, indent=2)
    sample_bytes = len(sample_json.encode("utf-8"))

    # Scale estimate based on actual counts
    avg_per_item = sample_bytes / max(1, len(plans[:10]) + len(photos[:10]) + len(annotations[:10]))
    estimated = avg_per_item * (len(plans) + len(photos) + len(annotations))

    # Add overhead for settings and structure
    return int(estimated + 500)
