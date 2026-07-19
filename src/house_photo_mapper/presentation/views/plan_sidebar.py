"""PlanSidebar - Multi-page navigation sidebar with thumbnails and page names."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QPixmap, QIcon, QAction, QFontMetrics, QPen, QBrush
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QMenu,
    QInputDialog,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QApplication,
    QStyle,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap


class PageItemWidget(QWidget):
    """Widget displayed for each page in the sidebar: thumbnail + arrows + name."""

    move_up_clicked = Signal(int)
    move_down_clicked = Signal(int)

    def __init__(self, page_num: int, pixmap: QPixmap, name: str, parent=None):
        super().__init__(parent)
        self._page_num = page_num
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        # Thumbnail
        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(120, 120)
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_label.setStyleSheet("background-color: palette(base);")
        scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._thumb_label.setPixmap(scaled)
        layout.addWidget(self._thumb_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Up/Down arrows
        arrow_layout = QHBoxLayout()
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.setSpacing(2)
        arrow_layout.addStretch()

        self._up_btn = QToolButton()
        self._up_btn.setText("\u25B2")  # ▲
        self._up_btn.setFixedSize(28, 18)
        self._up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self._page_num))
        arrow_layout.addWidget(self._up_btn)

        self._down_btn = QToolButton()
        self._down_btn.setText("\u25BC")  # ▼
        self._down_btn.setFixedSize(28, 18)
        self._down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self._page_num))
        arrow_layout.addWidget(self._down_btn)

        arrow_layout.addStretch()

        layout.addLayout(arrow_layout)

        # Page name
        self._name_label = QLabel(name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._name_label.setFixedWidth(120)
        layout.addWidget(self._name_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def update_button_states(self, is_first: bool, is_last: bool) -> None:
        """Enable/disable arrow buttons based on position in list."""
        self._up_btn.setEnabled(not is_first)
        self._down_btn.setEnabled(not is_last)

    def set_selected(self, selected: bool) -> None:
        """Update visual selection state."""
        if selected:
            self._thumb_label.setStyleSheet("border: 2px solid palette(highlight); border-radius: 3px; background-color: palette(base);")
        else:
            self._thumb_label.setStyleSheet("background-color: palette(base);")

    def update_thumbnail(self, pixmap: QPixmap) -> None:
        """Update the thumbnail with a new pixmap."""
        scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._thumb_label.setPixmap(scaled)


class PlanSidebar(QListWidget):
    """Sidebar widget displaying plan pages as thumbnails with page names.

    Features:
    - Custom widget per item with thumbnail, up/down arrows, and page name
    - Move Up/Move Down for reordering via arrow buttons or context menu
    - Context menu for rename and delete
    - Signals for order_changed, page_name_changed, page_deleted
    """

    # Emits list of dicts: [{page_num, order}, ...] in current display order
    order_changed = Signal(list)

    # Emits (page_num, name) when page is renamed
    page_name_changed = Signal(int, str)

    # Emits page_num when page delete is requested
    page_deleted = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize PlanSidebar with thumbnail display settings."""
        super().__init__(parent)

        # List mode for vertical item display with widgets
        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setFlow(QListWidget.Flow.TopToBottom)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSpacing(0)

        # Disable drag-drop (reordering via buttons/context menu only)
        self.setDragEnabled(False)

        # Store widgets by page_num for refresh after swaps
        self._page_widgets: dict[int, PageItemWidget] = {}

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Enable double-click to rename
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def clear(self) -> None:
        """Clear all items and widgets."""
        self._page_widgets.clear()
        super().clear()

    def add_page(self, page_num: int, pixmap: QPixmap, name: str = "") -> None:
        """Add a page to the sidebar with thumbnail, arrows, and name.

        Args:
            page_num: Globally unique page number.
            pixmap: Thumbnail pixmap for the page.
            name: User-assigned page name (empty = auto-generated).
        """
        display_name = name if name else f"Page {page_num + 1}"

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, page_num)
        item.setData(Qt.ItemDataRole.UserRole + 1, display_name)
        item.setSizeHint(QSize(130, 160))
        self.addItem(item)

        widget = PageItemWidget(page_num, pixmap, display_name)
        widget.move_up_clicked.connect(self.move_page_up)
        widget.move_down_clicked.connect(self.move_page_down)
        self._page_widgets[page_num] = widget
        self.setItemWidget(item, widget)

        self._update_button_states()

    def _show_context_menu(self, pos) -> None:
        """Show context menu for the item under the cursor.

        Args:
            pos: Position in viewport coordinates.
        """
        item = self.itemAt(pos)
        if item is None:
            return

        page_num = item.data(Qt.ItemDataRole.UserRole)
        row = self.row(item)

        menu = QMenu(self)

        # Move Up/Move Down actions
        move_up_action = QAction("Move Up", self)
        move_up_action.setEnabled(row > 0)
        move_up_action.triggered.connect(lambda: self.move_page_up(page_num))
        menu.addAction(move_up_action)

        move_down_action = QAction("Move Down", self)
        move_down_action.setEnabled(row < self.count() - 1)
        move_down_action.triggered.connect(lambda: self.move_page_down(page_num))
        menu.addAction(move_down_action)

        menu.addSeparator()

        rename_action = QAction("Rename Page...", self)
        rename_action.triggered.connect(lambda: self._rename_page(item))
        menu.addAction(rename_action)

        menu.addSeparator()

        delete_action = QAction("Delete Page", self)
        delete_action.triggered.connect(lambda: self._delete_page(page_num))
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(pos))

    def _rename_page(self, item: QListWidgetItem) -> None:
        """Open rename dialog for the given item.

        Args:
            item: The list item to rename.
        """
        page_num = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.data(Qt.ItemDataRole.UserRole + 1) or ""

        name, ok = QInputDialog.getText(
            self,
            "Rename Page",
            "Page name:",
            QLineEdit.EchoMode.Normal,
            current_name,
        )
        if ok:
            display_name = name if name else f"Page {page_num + 1}"
            item.setData(Qt.ItemDataRole.UserRole + 1, display_name)
            # Update widget name label
            widget = self._page_widgets.get(page_num)
            if widget:
                widget._name_label.setText(display_name)
            self.page_name_changed.emit(page_num, name)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on item to rename.

        Args:
            item: The double-clicked list item.
        """
        self._rename_page(item)

    def _delete_page(self, page_num: int) -> None:
        """Emit page_deleted signal for the given page.

        Args:
            page_num: Globally unique page number to delete.
        """
        self.page_deleted.emit(page_num)

    def move_page_up(self, page_num: int) -> None:
        """Move a page one position up in the list.

        Args:
            page_num: Globally unique page number to move up.
        """
        item = self._find_item_by_page_num(page_num)
        if item is None:
            return
        row = self.row(item)
        if row <= 0:
            return
        self._swap_items(row, row - 1)
        self._emit_order_changed()
        self.set_active_page(page_num)

    def move_page_down(self, page_num: int) -> None:
        """Move a page one position down in the list.

        Args:
            page_num: Globally unique page number to move down.
        """
        item = self._find_item_by_page_num(page_num)
        if item is None:
            return
        row = self.row(item)
        if row >= self.count() - 1:
            return
        self._swap_items(row, row + 1)
        self._emit_order_changed()
        self.set_active_page(page_num)

    def _find_item_by_page_num(self, page_num: int) -> QListWidgetItem | None:
        """Find the list item for a given page_num.

        Args:
            page_num: Globally unique page number to find.

        Returns:
            The matching QListWidgetItem, or None if not found.
        """
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == page_num:
                return item
        return None

    def _swap_items(self, row1: int, row2: int) -> None:
        """Move an item from one row to another using the model API.

        Args:
            row1: Source row index.
            row2: Destination row index.
        """
        from PySide6.QtCore import QModelIndex
        parent = QModelIndex()
        if row1 < row2:
            self.model().moveRow(parent, row1, parent, row2 + 1)
        else:
            self.model().moveRow(parent, row1, parent, row2)
        self._refresh_item_widgets()
        self._update_button_states()

    def _refresh_item_widgets(self) -> None:
        """Re-assign widgets to items after reordering."""
        for i in range(self.count()):
            item = self.item(i)
            page_num = item.data(Qt.ItemDataRole.UserRole)
            if page_num in self._page_widgets:
                self.setItemWidget(item, self._page_widgets[page_num])

    def _update_button_states(self) -> None:
        """Enable/disable up/down buttons based on each item's position."""
        count = self.count()
        for i in range(count):
            item = self.item(i)
            page_num = item.data(Qt.ItemDataRole.UserRole)
            widget = self._page_widgets.get(page_num)
            if widget:
                widget.update_button_states(is_first=(i == 0), is_last=(i == count - 1))

    def _emit_order_changed(self) -> None:
        """Emit order_changed with current page order."""
        order_list = []
        for i in range(self.count()):
            item = self.item(i)
            page_num = item.data(Qt.ItemDataRole.UserRole)
            order_list.append({
                "page_num": page_num,
                "order": i
            })
        self.order_changed.emit(order_list)

    def set_active_page(self, page_num: int) -> None:
        """Highlight the active page in the sidebar.

        Args:
            page_num: Page number to highlight (globally unique).
        """
        self.clearSelection()
        for i in range(self.count()):
            item = self.item(i)
            is_active = item.data(Qt.ItemDataRole.UserRole) == page_num
            item.setSelected(is_active)
            widget = self._page_widgets.get(item.data(Qt.ItemDataRole.UserRole))
            if widget:
                widget.set_selected(is_active)
            if is_active:
                self.scrollToItem(item)

    def update_page_thumbnail(self, page_num: int, pixmap) -> None:
        """Update the thumbnail for a specific page.

        Args:
            page_num: Globally unique page number.
            pixmap: New thumbnail pixmap.
        """
        widget = self._page_widgets.get(page_num)
        if widget:
            widget.update_thumbnail(pixmap)

    def get_page_order(self) -> list[dict]:
        """Get current page order from sidebar.

        Returns:
            List of dicts with page_num, order.
        """
        order_list = []
        for i in range(self.count()):
            item = self.item(i)
            page_num = item.data(Qt.ItemDataRole.UserRole)
            order_list.append({
                "page_num": page_num,
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
    sidebar.add_page(0, pixmap, name="Living Room")

    pixmap2 = QPixmap(200, 200)
    pixmap2.fill("blue")
    sidebar.add_page(1, pixmap2, name="Kitchen")

    pixmap3 = QPixmap(200, 200)
    pixmap3.fill("green")
    sidebar.add_page(2, pixmap3, name="Basement")

    sidebar.show()
    print("PlanSidebar created successfully")
    sys.exit(app.exec())
