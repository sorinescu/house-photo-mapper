"""PlanSidebar - Multi-page navigation sidebar with thumbnails, drag-reorder, and floor assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QComboBox, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap


class PlanSidebar(QListWidget):
    """Sidebar widget displaying plan pages as thumbnails with floor assignment.

    Features per RESEARCH.md Pattern 6:
    - IconMode for thumbnail display
    - InternalMove drag-drop for reordering
    - QComboBox per item for floor selection (-2 to 10)
    - Signals for order_changed and floor_changed
    """

    # Emits list of dicts: [{page_num, floor, order}, ...] in current display order
    order_changed = Signal(list)

    # Emits (page_num, floor) when floor combo changes
    floor_changed = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize PlanSidebar with drag-reorder and thumbnail settings."""
        super().__init__(parent)

        # IconMode for thumbnail grid display
        self.setViewMode(QListWidget.ViewMode.IconMode)

        # Icon size for thumbnails
        self.setIconSize(QSize(120, 120))

        # Layout settings
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)

        # Enable drag and set InternalMove for drag-reorder
        # Must be set AFTER setMovement(Static) because Static resets DragDropMode
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        # Connect model rowsMoved to emit order_changed
        self.model().rowsMoved.connect(self._on_rows_moved)

    def add_page(self, page_num: int, pixmap: QPixmap, floor: int = 0) -> None:
        """Add a page to the sidebar with thumbnail and floor combo.

        Args:
            page_num: Page number (0-based index in source document).
            pixmap: Thumbnail pixmap for the page.
            floor: Floor number (-2 to 10).
        """
        item = QListWidgetItem()

        # Scale pixmap to icon size keeping aspect ratio
        scaled_pixmap = pixmap.scaled(
            120, 120,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        item.setIcon(QIcon(scaled_pixmap))
        item.setText(f"Page {page_num + 1}")

        # Store page data in UserRole for retrieval
        item.setData(Qt.ItemDataRole.UserRole, {"page_num": page_num, "floor": floor})

        self.addItem(item)

        # Add floor combo box as item widget
        self._add_floor_combo(item, floor)

    def _add_floor_combo(self, item: QListWidgetItem, floor: int) -> None:
        """Add floor selection combo box to item.

        Args:
            item: The list widget item.
            floor: Initial floor value (-2 to 10).
        """
        combo = QComboBox()
        # Floors -2 (Basement 2) to 10
        for f in range(-2, 11):
            combo.addItem(f"Floor {f}")
        # Floor -2 is index 0, Floor 0 is index 2, Floor 10 is index 12
        combo.setCurrentIndex(floor + 2)

        # Store page_num in combo for signal emission
        combo.setProperty("page_num", item.data(Qt.ItemDataRole.UserRole)["page_num"])

        # Connect combo change to signal
        combo.currentIndexChanged.connect(
            lambda idx: self._on_floor_changed(item, idx)
        )

        self.setItemWidget(item, combo)

    def _on_floor_changed(self, item: QListWidgetItem, combo_index: int) -> None:
        """Handle floor combo change.

        Args:
            item: The list item whose combo changed.
            combo_index: New combo box index (0 = Floor -2, 12 = Floor 10).
        """
        data = item.data(Qt.ItemDataRole.UserRole)
        page_num = data["page_num"]
        floor = combo_index - 2  # Convert combo index to floor number

        # Update stored floor
        data["floor"] = floor
        item.setData(Qt.ItemDataRole.UserRole, data)

        # Emit signal
        self.floor_changed.emit(page_num, floor)

    def _on_rows_moved(self, parent, start: int, end: int, destination, row: int) -> None:
        """Handle drag-reorder and emit order_changed with full page list.

        Args:
            parent: Source parent index (unused).
            start: Start row of moved items.
            end: End row of moved items.
            destination: Destination parent index (unused).
            row: Destination row.
        """
        order_list = []
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            order_list.append({
                "page_num": data["page_num"],
                "floor": data["floor"],
                "order": i
            })
        self.order_changed.emit(order_list)

    def set_active_page(self, page_num: int) -> None:
        """Highlight the active page in the sidebar.

        Args:
            page_num: Page number to highlight (0-based source index).
        """
        self.clearSelection()
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data["page_num"] == page_num:
                item.setSelected(True)
                self.scrollToItem(item)
                break

    def update_page_order(self, new_order: list[dict]) -> None:
        """Reorder sidebar items to match new order from PlanModel.

        Args:
            new_order: List of dicts with page_num, floor, order.
        """
        # Build mapping from page_num to item
        page_to_item = {}
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            page_to_item[data["page_num"]] = item

        # Reorder items in the list
        # We need to take items and re-insert them in new order
        for i, page_data in enumerate(new_order):
            page_num = page_data["page_num"]
            if page_num in page_to_item:
                item = page_to_item[page_num]
                # Take item out and re-insert at correct position
                row = self.row(item)
                if row != i:
                    taken = self.takeItem(row)
                    self.insertItem(i, taken)
                    # Update order in item data
                    data = taken.data(Qt.ItemDataRole.UserRole)
                    data["order"] = i
                    taken.setData(Qt.ItemDataRole.UserRole, data)

    def get_page_order(self) -> list[dict]:
        """Get current page order from sidebar.

        Returns:
            List of dicts with page_num, floor, order.
        """
        order_list = []
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            order_list.append({
                "page_num": data["page_num"],
                "floor": data["floor"],
                "order": i
            })
        return order_list


if __name__ == "__main__":
    # Quick manual test
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    sidebar = PlanSidebar()

    # Add some test pages
    pixmap = QPixmap(200, 200)
    pixmap.fill("red")
    sidebar.add_page(0, pixmap, floor=0)

    pixmap2 = QPixmap(200, 200)
    pixmap2.fill("blue")
    sidebar.add_page(1, pixmap2, floor=1)

    pixmap3 = QPixmap(200, 200)
    pixmap3.fill("green")
    sidebar.add_page(2, pixmap3, floor=-1)

    sidebar.show()
    print("PlanSidebar created successfully")
    sys.exit(app.exec())