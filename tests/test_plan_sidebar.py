"""Tests for PlanSidebar - multi-page navigation with drag-reorder and floor assignment."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, QPointF, QRectF, QEvent, QPoint, QSize
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QComboBox, QWidget
from PySide6.QtGui import QPixmap, QIcon, QImage, QColor

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from house_photo_mapper.presentation.views.plan_sidebar import PlanSidebar


class TestPlanSidebar:
    """Tests for PlanSidebar widget."""

    def test_sidebar_creation(self, qapp):
        """Test PlanSidebar instantiates correctly."""
        sidebar = PlanSidebar()
        assert isinstance(sidebar, QListWidget)

    def test_sidebar_configuration(self, qapp):
        """Test PlanSidebar is configured per RESEARCH.md Pattern 6."""
        sidebar = PlanSidebar()

        # IconMode for thumbnail display
        assert sidebar.viewMode() == QListWidget.ViewMode.IconMode

        # InternalMove for drag-reorder
        assert sidebar.dragDropMode() == QListWidget.DragDropMode.InternalMove
        assert sidebar.defaultDropAction() == Qt.DropAction.MoveAction

        # Icon size 120x120
        icon_size = sidebar.iconSize()
        assert icon_size.width() == 120
        assert icon_size.height() == 120

        # Resize mode Adjust
        assert sidebar.resizeMode() == QListWidget.ResizeMode.Adjust

        # Movement Static (items don't move during drag except for reorder)
        assert sidebar.movement() == QListWidget.Movement.Static

    def test_add_page_creates_item_with_thumbnail(self, qapp):
        """Test add_page creates QListWidgetItem with icon and text."""
        sidebar = PlanSidebar()

        # Create a test pixmap
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))

        sidebar.add_page(0, pixmap, floor=0)

        assert sidebar.count() == 1
        item = sidebar.item(0)
        assert item is not None
        assert item.text() == "Page 1"
        assert not item.icon().isNull()
        # Icon should be scaled to 120x120
        assert item.icon().availableSizes()[0].width() <= 120

    def test_add_page_stores_page_data_in_user_role(self, qapp):
        """Test add_page stores page_num and floor in UserRole data."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("blue"))

        sidebar.add_page(2, pixmap, floor=1)

        item = sidebar.item(0)
        data = item.data(Qt.ItemDataRole.UserRole)
        assert data is not None
        assert data["page_num"] == 2
        assert data["floor"] == 1

    def test_add_page_creates_floor_combo_box(self, qapp):
        """Test add_page creates QComboBox with floors -2 to 10."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("green"))

        sidebar.add_page(0, pixmap, floor=0)

        item = sidebar.item(0)
        combo = sidebar.itemWidget(item)
        assert isinstance(combo, QComboBox)

        # Should have 13 items: Floor -2 (Basement 2) to Floor 10
        assert combo.count() == 13
        # Check first and last items
        assert combo.itemText(0) == "Floor -2"
        assert combo.itemText(12) == "Floor 10"

    def test_floor_combo_initial_selection(self, qapp):
        """Test floor combo starts at correct index for given floor."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("yellow"))

        # Floor 0 -> index 2 (Floor -2 is index 0, Floor -1 is index 1, Floor 0 is index 2)
        sidebar.add_page(0, pixmap, floor=0)
        item = sidebar.item(0)
        combo = sidebar.itemWidget(item)
        assert combo.currentIndex() == 2

        # Floor -2 -> index 0
        sidebar.add_page(1, pixmap, floor=-2)
        item = sidebar.item(1)
        combo = sidebar.itemWidget(item)
        assert combo.currentIndex() == 0

        # Floor 10 -> index 12
        sidebar.add_page(2, pixmap, floor=10)
        item = sidebar.item(2)
        combo = sidebar.itemWidget(item)
        assert combo.currentIndex() == 12

    def test_floor_combo_change_emits_floor_changed_signal(self, qapp):
        """Test floor combo change emits floor_changed(page_num, floor)."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("cyan"))

        sidebar.add_page(0, pixmap, floor=0)

        emitted_signals = []
        sidebar.floor_changed.connect(lambda page_num, floor: emitted_signals.append((page_num, floor)))

        item = sidebar.item(0)
        combo = sidebar.itemWidget(item)

        # Change floor from 0 (index 2) to 1 (index 3)
        combo.setCurrentIndex(3)

        assert len(emitted_signals) == 1
        assert emitted_signals[0] == (0, 1)  # page_num=0, floor=1

    def test_drag_reorder_emits_order_changed_signal(self, qapp):
        """Test drag-reorder emits order_changed with full page list."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("magenta"))

        # Add 3 pages
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)

        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        # Actually move item 2 to position 0 (simulating what Qt does during drag-drop)
        item2 = sidebar.takeItem(2)  # Remove from position 2
        sidebar.insertItem(0, item2)  # Insert at position 0

        # Now emit the signal to notify observers
        # rowsMoved signal: parent, start, end, destination, row
        model = sidebar.model()
        model.rowsMoved.emit(None, 2, 2, None, 0)

        assert len(emitted_orders) == 1
        order_list = emitted_orders[0]
        assert len(order_list) == 3
        # New order should be: page 2, page 0, page 1
        assert order_list[0]["page_num"] == 2
        assert order_list[1]["page_num"] == 0
        assert order_list[2]["page_num"] == 1
        # Check order field is updated
        assert order_list[0]["order"] == 0
        assert order_list[1]["order"] == 1
        assert order_list[2]["order"] == 2

    def test_set_active_page_highlights_item(self, qapp):
        """Test set_active_page selects the correct item."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("white"))

        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)

        # Initially no selection
        assert len(sidebar.selectedItems()) == 0

        sidebar.set_active_page(1)

        selected = sidebar.selectedItems()
        assert len(selected) == 1
        data = selected[0].data(Qt.ItemDataRole.UserRole)
        assert data["page_num"] == 1

    def test_set_active_page_invalid_does_nothing(self, qapp):
        """Test set_active_page with invalid page_num does nothing."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("black"))

        sidebar.add_page(0, pixmap, floor=0)

        # Should not raise or crash
        sidebar.set_active_page(999)
        assert len(sidebar.selectedItems()) == 0

    def test_update_page_order_reorders_items(self, qapp):
        """Test update_page_order reorders items to match new order list."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("gray"))

        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)

        # New order: page 2, page 0, page 1
        new_order = [
            {"page_num": 2, "floor": 2, "order": 0},
            {"page_num": 0, "floor": 0, "order": 1},
            {"page_num": 1, "floor": 1, "order": 2},
        ]

        sidebar.update_page_order(new_order)

        assert sidebar.item(0).data(Qt.ItemDataRole.UserRole)["page_num"] == 2
        assert sidebar.item(1).data(Qt.ItemDataRole.UserRole)["page_num"] == 0
        assert sidebar.item(2).data(Qt.ItemDataRole.UserRole)["page_num"] == 1

    def test_thumbnail_scaled_correctly(self, qapp):
        """Test thumbnails are scaled to 120x120 keeping aspect ratio."""
        sidebar = PlanSidebar()

        # Create a non-square pixmap
        pixmap = QPixmap(400, 200)  # 2:1 aspect ratio
        pixmap.fill(QColor("orange"))

        sidebar.add_page(0, pixmap, floor=0)

        item = sidebar.item(0)
        icon = item.icon()
        sizes = icon.availableSizes()
        assert len(sizes) > 0
        size = sizes[0]
        # Should fit within 120x120
        assert size.width() <= 120
        assert size.height() <= 120

    def test_plan_sidebar_drag_reorder(self, qapp):
        """Test drag-reorder changes page order and emits order_changed with correct list."""
        sidebar = PlanSidebar()

        # Create 3 pages with different floors
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)

        # Verify initial order
        assert sidebar.item(0).data(Qt.ItemDataRole.UserRole)["page_num"] == 0
        assert sidebar.item(1).data(Qt.ItemDataRole.UserRole)["page_num"] == 1
        assert sidebar.item(2).data(Qt.ItemDataRole.UserRole)["page_num"] == 2

        # Track emitted signals
        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        # Simulate drag-reorder: move page 2 to position 0
        item2 = sidebar.takeItem(2)
        sidebar.insertItem(0, item2)

        # Emit rowsMoved signal (what Qt does internally during drag-drop)
        model = sidebar.model()
        model.rowsMoved.emit(None, 2, 2, None, 0)

        # Verify order changed signal emitted
        assert len(emitted_orders) == 1
        order_list = emitted_orders[0]

        # Verify new order matches what we moved
        assert len(order_list) == 3
        assert order_list[0]["page_num"] == 2  # Moved to front
        assert order_list[1]["page_num"] == 0
        assert order_list[2]["page_num"] == 1

        # Verify order field updated correctly
        assert order_list[0]["order"] == 0
        assert order_list[1]["order"] == 1
        assert order_list[2]["order"] == 2

        # Verify floor values preserved
        assert order_list[0]["floor"] == 2
        assert order_list[1]["floor"] == 0
        assert order_list[2]["floor"] == 1


class TestPlanSidebarIntegration:
    """Integration tests for PlanSidebar with PlanViewModel."""

    def test_sidebar_viewmodel_page_click_switches_page(self, qapp):
        """Test clicking sidebar page emits itemClicked -> set_page."""
        from PySide6.QtCore import QModelIndex
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0, floor=0),
            PageModel(source_path="test.pdf", page_index=1, order=1, floor=1),
            PageModel(source_path="test.pdf", page_index=2, order=2, floor=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect sidebar item click to ViewModel
        sidebar.itemClicked.connect(lambda item: vm.on_sidebar_page_clicked(
            item.data(Qt.ItemDataRole.UserRole)["page_num"]
        ))
        
        # Track page changes
        page_changes = []
        vm.page_changed.connect(lambda idx: page_changes.append(idx))
        
        # Click on page 2 (index 1)
        item = sidebar.item(1)
        sidebar.setCurrentItem(item)
        sidebar.itemClicked.emit(item)
        
        # Verify page changed
        assert len(page_changes) == 1
        assert page_changes[0] == 1
        assert vm.current_page == 1

    def test_sidebar_viewmodel_reorder_updates_model(self, qapp):
        """Test sidebar reorder -> PlanViewModel.on_sidebar_order_changed -> PlanModel updated."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0, floor=0),
            PageModel(source_path="test.pdf", page_index=1, order=1, floor=1),
            PageModel(source_path="test.pdf", page_index=2, order=2, floor=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect sidebar order change to ViewModel
        sidebar.order_changed.connect(vm.on_sidebar_order_changed)
        
        # Track pages reordered signal
        pages_reordered_received = []
        vm.pages_reordered.connect(lambda pages: pages_reordered_received.append(pages))
        
        # Simulate drag-reorder: move page 2 to position 0
        item2 = sidebar.takeItem(2)
        sidebar.insertItem(0, item2)
        
        # Emit rowsMoved signal
        model_qt = sidebar.model()
        model_qt.rowsMoved.emit(None, 2, 2, None, 0)
        
        # Verify ViewModel updated model order
        sorted_pages = vm.get_sorted_pages()
        assert sorted_pages[0].page_index == 2  # Moved to front
        assert sorted_pages[1].page_index == 0
        assert sorted_pages[2].page_index == 1
        
        # Verify order field updated
        assert sorted_pages[0].order == 0
        assert sorted_pages[1].order == 1
        assert sorted_pages[2].order == 2
        
        # Verify pages_reordered signal emitted
        assert len(pages_reordered_received) == 1

    def test_sidebar_viewmodel_floor_change_updates_model(self, qapp):
        """Test floor combo change -> PlanViewModel.on_sidebar_floor_changed -> PageModel.floor updated."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0, floor=0),
            PageModel(source_path="test.pdf", page_index=1, order=1, floor=1),
            PageModel(source_path="test.pdf", page_index=2, order=2, floor=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect sidebar floor change to ViewModel
        sidebar.floor_changed.connect(vm.on_sidebar_floor_changed)
        
        # Track floor changed signal
        floor_changes = []
        vm.floor_changed.connect(lambda page_num, floor: floor_changes.append((page_num, floor)))
        
        # Change floor on page 0 from 0 to 5
        item = sidebar.item(0)
        combo = sidebar.itemWidget(item)
        combo.setCurrentIndex(7)  # Index 7 = Floor 5 (7-2=5)
        
        # Verify ViewModel updated model floor
        sorted_pages = vm.get_sorted_pages()
        assert sorted_pages[0].floor == 5
        
        # Verify floor_changed signal emitted
        assert len(floor_changes) == 1
        assert floor_changes[0] == (0, 5)  # page_num=0, floor=5

    def test_viewmodel_page_changed_highlights_sidebar(self, qapp):
        """Test PlanViewModel.page_changed -> PlanSidebar.set_active_page."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0, floor=0),
            PageModel(source_path="test.pdf", page_index=1, order=1, floor=1),
            PageModel(source_path="test.pdf", page_index=2, order=2, floor=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect ViewModel page_changed to sidebar set_active_page
        vm.page_changed.connect(sidebar.set_active_page)
        
        # Set page to 2
        vm.set_page(2)
        
        # Verify sidebar highlights page 2
        selected = sidebar.selectedItems()
        assert len(selected) == 1
        data = selected[0].data(Qt.ItemDataRole.UserRole)
        assert data["page_num"] == 2

    def test_sidebar_viewmodel_integration(self, qapp):
        """Test full integration: sidebar click -> ViewModel -> model updated -> sidebar highlight."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap, floor=0)
        sidebar.add_page(1, pixmap, floor=1)
        sidebar.add_page(2, pixmap, floor=2)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0, floor=0),
            PageModel(source_path="test.pdf", page_index=1, order=1, floor=1),
            PageModel(source_path="test.pdf", page_index=2, order=2, floor=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect signals
        sidebar.itemClicked.connect(lambda item: vm.on_sidebar_page_clicked(
            item.data(Qt.ItemDataRole.UserRole)["page_num"]
        ))
        vm.page_changed.connect(sidebar.set_active_page)
        
        # Click on page 1
        item = sidebar.item(1)
        sidebar.setCurrentItem(item)
        sidebar.itemClicked.emit(item)
        
        # Verify sidebar highlights page 1
        selected = sidebar.selectedItems()
        assert len(selected) == 1
        data = selected[0].data(Qt.ItemDataRole.UserRole)
        assert data["page_num"] == 1
        
        # Verify ViewModel page changed
        assert vm.current_page == 1


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
