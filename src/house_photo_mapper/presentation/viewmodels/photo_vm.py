"""PhotoViewModel - Manages photo collection and thumbnail generation."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QPixmap

from house_photo_mapper.domain.models.photo import PhotoModel
from house_photo_mapper.domain.services.duplicate_detector import detect_duplicates, mark_duplicates
from house_photo_mapper.domain.services.photo_importer import import_photos
from house_photo_mapper.domain.services.thumbnail_generator import ThumbnailGenerator
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel

if TYPE_CHECKING:
    pass


class PhotoViewModel(QtSafeViewModel):
    """ViewModel for photo collection management.

    Handles photo import, thumbnail generation, duplicate detection,
    and selection state for the photo browser UI.
    """

    photo_added = Signal(object)  # PhotoModel
    photo_removed = Signal(str)  # path
    thumbnail_ready = Signal(str, QPixmap)  # path, pixmap
    duplicates_found = Signal(list)  # list[DuplicateGroup]
    selection_changed = Signal(object)  # PhotoModel or None
    metadata_changed = Signal(dict)  # display metadata dict
    photos_changed = Signal()  # emitted when photo list changes

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize PhotoViewModel.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._photos: list[PhotoModel] = []
        self._selected_photo: PhotoModel | None = None
        self._thumbnail_generator = ThumbnailGenerator(parent=self)
        self._thumbnail_generator.thumbnail_ready.connect(self._on_thumbnail_ready)

    @property
    def photos(self) -> list[PhotoModel]:
        """Return current photo list."""
        return self._photos

    @property
    def selected_photo(self) -> PhotoModel | None:
        """Return currently selected photo."""
        return self._selected_photo

    @Slot(list)
    def import_photos(self, paths: list[str], project_dir: str | None = None) -> None:
        """Import photos from file paths.

        Args:
            paths: List of photo file paths to import.
            project_dir: Project directory for computing relative paths.
        """
        if not paths:
            return

        # Import photos
        photo_paths = [Path(p) for p in paths]
        if project_dir:
            new_photos = import_photos(photo_paths, Path(project_dir))
        else:
            # Use current directory if no project dir specified
            new_photos = import_photos(photo_paths, Path.cwd())

        # Add to collection
        for photo in new_photos:
            self._photos.append(photo)
            self.photo_added.emit(photo)

            # Generate thumbnail
            if project_dir:
                full_path = str(Path(project_dir) / photo.path)
            else:
                full_path = photo.path
            self._thumbnail_generator.generate(full_path)

        # Detect duplicates
        if len(self._photos) > 1:
            groups = detect_duplicates(self._photos, project_dir)
            if groups:
                mark_duplicates(self._photos, groups)
                self.duplicates_found.emit(groups)

        self.photos_changed.emit()

    @Slot(str)
    def select_photo(self, path: str) -> None:
        """Select a photo by path.

        Args:
            path: Path of photo to select.
        """
        for photo in self._photos:
            if photo.path == path:
                self._selected_photo = photo
                self.selection_changed.emit(photo)
                self.metadata_changed.emit(photo.display_metadata())
                return

        # Not found
        self._selected_photo = None
        self.selection_changed.emit(None)
        self.metadata_changed.emit({})

    @Slot()
    def remove_selected(self) -> None:
        """Remove the currently selected photo."""
        if self._selected_photo is None:
            return

        path = self._selected_photo.path
        self._photos = [p for p in self._photos if p.path != path]
        self._selected_photo = None
        self.photo_removed.emit(path)
        self.selection_changed.emit(None)
        self.metadata_changed.emit({})
        self.photos_changed.emit()

    @Slot()
    def review_duplicates(self) -> None:
        """Open duplicate review dialog (placeholder for now)."""
        # TODO: Implement duplicate review dialog in future plan
        pass

    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap) -> None:
        """Handle thumbnail generation completion."""
        self.thumbnail_ready.emit(path, pixmap)

    def get_thumbnail(self, path: str) -> QPixmap | None:
        """Get cached thumbnail for a path.

        Args:
            path: Source image path.

        Returns:
            Cached QPixmap or None.
        """
        return self._thumbnail_generator.get_cached(path)
