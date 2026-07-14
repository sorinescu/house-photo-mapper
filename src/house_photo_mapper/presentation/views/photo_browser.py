"""PhotoBrowser - Widget for browsing photos with thumbnails."""

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget


class PhotoBrowser(QListWidget):
    """Photo browser widget with icon mode and lazy loading.

    Displays photos in a grid with thumbnails. Supports duplicate badges
    and lazy thumbnail generation for visible items.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize PhotoBrowser.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(200, 200))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(10)
        self.setGridSize(QSize(220, 240))
        self.setWrapping(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    @Slot(str, QPixmap)
    def add_photo(self, path: str, thumbnail: QPixmap | None = None) -> None:
        """Add a photo item to the browser.

        Args:
            path: Photo file path.
            thumbnail: Optional thumbnail pixmap.
        """
        item = QListWidgetItem(self)
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setText(path.split("/")[-1])  # Show filename

        if thumbnail and not thumbnail.isNull():
            item.setIcon(QIcon(thumbnail))
        else:
            # Placeholder
            placeholder = QPixmap(200, 200)
            placeholder.fill(Qt.GlobalColor.lightGray)
            item.setIcon(QIcon(placeholder))

        self.addItem(item)

    @Slot(str, QPixmap)
    def update_thumbnail(self, path: str, pixmap: QPixmap) -> None:
        """Update thumbnail for a photo.

        Args:
            path: Photo file path.
            pixmap: New thumbnail pixmap.
        """
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                item.setIcon(QIcon(pixmap))
                break

    @Slot(str, str)
    def mark_duplicate(self, path: str, group_id: str) -> None:
        """Mark a photo as duplicate with badge.

        Args:
            path: Photo file path.
            group_id: Duplicate group ID.
        """
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                # Add duplicate badge to text
                item.setText(f"{path.split('/')[-1]}\n[Duplicate: {group_id}]")
                break

    @Slot(str)
    def remove_photo(self, path: str) -> None:
        """Remove a photo from the browser.

        Args:
            path: Photo file path.
        """
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.takeItem(i)
                break

    def clear(self) -> None:
        """Clear all photos from the browser."""
        super().clear()
