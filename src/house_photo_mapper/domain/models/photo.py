"""Photo domain models: PhotoModel, ExifModel, DuplicateGroup."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class ExifModel(BaseModel):
    """EXIF metadata extracted from a photo.

    Attributes:
        timestamp: When the photo was taken (from EXIF DateTimeOriginal).
        camera_make: Camera manufacturer (e.g., "Apple", "Canon").
        camera_model: Camera model (e.g., "iPhone 15 Pro", "EOS R5").
        lens_model: Lens model (e.g., "iPhone 15 Pro back triple camera").
        orientation: EXIF orientation (1-8) for correct display rotation.
        gps_lat: GPS latitude in decimal degrees (positive = North).
        gps_lon: GPS longitude in decimal degrees (positive = East).
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    timestamp: Optional[datetime] = Field(default=None, description="When photo was taken")
    camera_make: Optional[str] = Field(default=None, description="Camera manufacturer")
    camera_model: Optional[str] = Field(default=None, description="Camera model")
    lens_model: Optional[str] = Field(default=None, description="Lens model")
    orientation: int = Field(default=1, ge=1, le=8, description="EXIF orientation (1-8)")
    gps_lat: Optional[float] = Field(default=None, description="GPS latitude (decimal degrees)")
    gps_lon: Optional[float] = Field(default=None, description="GPS longitude (decimal degrees)")


class DuplicateGroup(BaseModel):
    """Group of photos detected as duplicates via perceptual hashing.

    Attributes:
        group_id: Unique identifier for this duplicate group.
        photo_paths: List of file paths belonging to this group.
        representative_index: Index of the recommended representative photo.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    group_id: str = Field(description="Unique group identifier")
    photo_paths: list[str] = Field(min_length=2, description="Paths of duplicate photos")
    representative_index: int = Field(default=0, ge=0, description="Index of representative photo")


class PhotoModel(BaseModel):
    """Photo model with metadata, hash, and duplicate tracking.

    Attributes:
        path: Path to photo file, relative to project directory.
        filename: Original filename.
        original_path: Original absolute path when imported.
        file_size: File size in bytes.
        width: Image width in pixels.
        height: Image height in pixels.
        exif: Optional EXIF metadata.
        perceptual_hash: Perceptual hash string for duplicate detection.
        is_duplicate: Whether this photo is flagged as a duplicate.
        duplicate_group_id: ID of duplicate group if is_duplicate is True.
        imported_at: Timestamp when photo was imported.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    path: str = Field(description="Relative path from project root")
    filename: str = Field(description="Original filename")
    original_path: str = Field(default="", description="Original absolute path when imported")
    file_size: int = Field(ge=0, description="File size in bytes")
    width: int = Field(gt=0, description="Image width in pixels")
    height: int = Field(gt=0, description="Image height in pixels")
    exif: Optional[ExifModel] = Field(default=None, description="EXIF metadata")
    perceptual_hash: str = Field(default="", description="Perceptual hash for duplicates")
    is_duplicate: bool = Field(default=False, description="Flagged as duplicate")
    duplicate_group_id: Optional[str] = Field(default=None, description="Duplicate group ID")
    imported_at: datetime = Field(default_factory=datetime.now, description="Import timestamp")

    def to_project_json(self) -> dict:
        """Serialize photo model to JSON-compatible dict for project persistence.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_project_json(cls, data: dict) -> "PhotoModel":
        """Deserialize photo model from project JSON data.

        Args:
            data: Dictionary from JSON deserialization.

        Returns:
            Validated PhotoModel instance.
        """
        return cls.model_validate(data)

    def display_metadata(self) -> dict:
        """Get a dictionary of metadata for UI display.

        Returns:
            Dictionary with human-readable metadata fields.
        """
        result = {
            "Filename": self.filename,
            "Size": f"{self.file_size / 1024:.1f} KB",
            "Dimensions": f"{self.width} × {self.height}",
        }

        if self.exif:
            if self.exif.camera_make and self.exif.camera_model:
                result["Camera"] = f"{self.exif.camera_make} {self.exif.camera_model}"
            elif self.exif.camera_make:
                result["Camera"] = self.exif.camera_make

            if self.exif.lens_model:
                result["Lens"] = self.exif.lens_model

            if self.exif.timestamp:
                result["Date"] = self.exif.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            if self.exif.gps_lat is not None and self.exif.gps_lon is not None:
                result["GPS"] = f"{self.exif.gps_lat:.6f}, {self.exif.gps_lon:.6f}"

        if self.is_duplicate:
            result["Duplicate"] = f"Group {self.duplicate_group_id}"

        return result


if __name__ == "__main__":
    # Quick manual test
    photo = PhotoModel(
        path="photos/test.jpg",
        filename="test.jpg",
        file_size=1024000,
        width=1920,
        height=1080,
    )
    print("Photo JSON:", photo.to_project_json())
