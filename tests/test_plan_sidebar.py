"""Tests for PlanSidebar - multi-page navigation with move reorder and page names."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, QPointF, QRectF, QEvent, QPoint, QSize
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget
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
        """Test PlanSidebar is configured for thumbnail display."""
        sidebar = PlanSidebar()

        # ListMode for thumbnail display with embedded widgets
        assert sidebar.viewMode() == QListWidget.ViewMode.ListMode

        # Drag disabled - reordering via buttons/context menu only
        assert not sidebar.dragEnabled()

        # Resize mode Adjust
        assert sidebar.resizeMode() == QListWidget.ResizeMode.Adjust

    def test_add_page_creates_item_with_widget(self, qapp):
        """Test add_page creates QListWidgetItem with PageItemWidget."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))

        sidebar.add_page(0, pixmap, name="")

        assert sidebar.count() == 1
        item = sidebar.item(0)
        assert item is not None
        # Check stored data
        assert item.data(Qt.ItemDataRole.UserRole) == 0
        assert item.data(Qt.ItemDataRole.UserRole + 1) == "Page 1"
        # Check widget is attached
        widget = sidebar.itemWidget(item)
        assert widget is not None

    def test_add_page_with_custom_name(self, qapp):
        """Test add_page with custom name shows name in widget."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("blue"))

        sidebar.add_page(0, pixmap, name="Living Room")

        item = sidebar.item(0)
        assert item.data(Qt.ItemDataRole.UserRole + 1) == "Living Room"
        widget = sidebar.itemWidget(item)
        assert widget is not None

    def test_add_page_stores_page_data_in_user_role(self, qapp):
        """Test add_page stores page_num in UserRole data."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("blue"))

        sidebar.add_page(2, pixmap, name="Kitchen")

        item = sidebar.item(0)
        page_num = item.data(Qt.ItemDataRole.UserRole)
        assert page_num == 2
        name = item.data(Qt.ItemDataRole.UserRole + 1)
        assert name == "Kitchen"

    def test_move_page_up_emits_order_changed(self, qapp):
        """Test move_page_up emits order_changed with full page list."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("magenta"))

        # Add 3 pages
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)

        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        # Move page 2 (at position 2) up twice to position 0
        sidebar.move_page_up(2)
        sidebar.move_page_up(2)

        assert len(emitted_orders) == 2
        order_list = emitted_orders[-1]
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

        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)

        # Initially no selection
        assert len(sidebar.selectedItems()) == 0

        sidebar.set_active_page(1)

        selected = sidebar.selectedItems()
        assert len(selected) == 1
        assert selected[0].data(Qt.ItemDataRole.UserRole) == 1

    def test_set_active_page_invalid_does_nothing(self, qapp):
        """Test set_active_page with invalid page_num does nothing."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("black"))

        sidebar.add_page(0, pixmap)

        # Should not raise or crash
        sidebar.set_active_page(999)
        assert len(sidebar.selectedItems()) == 0

    def test_thumbnail_in_widget(self, qapp):
        """Test thumbnails are displayed in the sidebar widget."""
        sidebar = PlanSidebar()

        # Create a non-square pixmap
        pixmap = QPixmap(400, 200)  # 2:1 aspect ratio
        pixmap.fill(QColor("orange"))

        sidebar.add_page(0, pixmap)

        item = sidebar.item(0)
        widget = sidebar.itemWidget(item)
        assert widget is not None
        # Widget should have a thumbnail label
        assert hasattr(widget, '_thumb_label')
        assert widget._thumb_label.pixmap() is not None

    def test_move_page_down_reorders_items(self, qapp):
        """Test move_page_down changes page order and emits order_changed with correct list."""
        sidebar = PlanSidebar()

        # Create 3 pages
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)

        # Verify initial order
        assert sidebar.item(0).data(Qt.ItemDataRole.UserRole) == 0
        assert sidebar.item(1).data(Qt.ItemDataRole.UserRole) == 1
        assert sidebar.item(2).data(Qt.ItemDataRole.UserRole) == 2

        # Track emitted signals
        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        # Move page 0 down twice to position 2
        sidebar.move_page_down(0)
        sidebar.move_page_down(0)

        # Verify order changed signal emitted
        assert len(emitted_orders) == 2
        order_list = emitted_orders[-1]

        # Verify new order matches what we moved
        assert len(order_list) == 3
        assert order_list[0]["page_num"] == 1  # Moved up
        assert order_list[1]["page_num"] == 2
        assert order_list[2]["page_num"] == 0  # Moved to end

        # Verify order field updated correctly
        assert order_list[0]["order"] == 0
        assert order_list[1]["order"] == 1
        assert order_list[2]["order"] == 2


    def test_move_page_up_first_item_noop(self, qapp):
        """Test move_page_up on first item does nothing."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)

        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        sidebar.move_page_up(0)

        assert len(emitted_orders) == 0
        assert sidebar.item(0).data(Qt.ItemDataRole.UserRole) == 0
        assert sidebar.item(1).data(Qt.ItemDataRole.UserRole) == 1

    def test_move_page_down_last_item_noop(self, qapp):
        """Test move_page_down on last item does nothing."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)

        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        sidebar.move_page_down(1)

        assert len(emitted_orders) == 0
        assert sidebar.item(0).data(Qt.ItemDataRole.UserRole) == 0
        assert sidebar.item(1).data(Qt.ItemDataRole.UserRole) == 1

    def test_move_page_up_invalid_page_noop(self, qapp):
        """Test move_page_up with non-existent page_num does nothing."""
        sidebar = PlanSidebar()

        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)

        emitted_orders = []
        sidebar.order_changed.connect(lambda order: emitted_orders.append(order))

        sidebar.move_page_up(999)

        assert len(emitted_orders) == 0


class TestPlanSidebarIntegration:
    """Integration tests for PlanSidebar with PlanViewModel."""

    def test_sidebar_viewmodel_page_click_switches_page(self, qapp):
        """Test clicking sidebar page emits itemClicked -> set_page."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0),
            PageModel(source_path="test.pdf", page_index=1, order=1),
            PageModel(source_path="test.pdf", page_index=2, order=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect sidebar item click to ViewModel
        sidebar.itemClicked.connect(lambda item: vm.on_sidebar_page_clicked(
            item.data(Qt.ItemDataRole.UserRole)
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
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0),
            PageModel(source_path="test.pdf", page_index=1, order=1),
            PageModel(source_path="test.pdf", page_index=2, order=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect sidebar order change to ViewModel
        sidebar.order_changed.connect(vm.on_sidebar_order_changed)
        
        # Track pages reordered signal
        pages_reordered_received = []
        vm.pages_reordered.connect(lambda pages: pages_reordered_received.append(pages))
        
        # Use move_page_up to move page 2 from position 2 to position 0
        sidebar.move_page_up(2)
        sidebar.move_page_up(2)
        
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
        assert len(pages_reordered_received) == 2

    def test_viewmodel_page_changed_highlights_sidebar(self, qapp):
        """Test PlanViewModel.page_changed -> PlanSidebar.set_active_page."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0),
            PageModel(source_path="test.pdf", page_index=1, order=1),
            PageModel(source_path="test.pdf", page_index=2, order=2),
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
        assert selected[0].data(Qt.ItemDataRole.UserRole) == 2

    def test_sidebar_viewmodel_integration(self, qapp):
        """Test full integration: sidebar click -> ViewModel -> model updated -> sidebar highlight."""
        from PySide6.QtGui import QPixmap, QColor
        from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
        from house_photo_mapper.domain.models.plan import PlanModel, PageModel
        
        # Create sidebar with 3 pages
        sidebar = PlanSidebar()
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor("red"))
        sidebar.add_page(0, pixmap)
        sidebar.add_page(1, pixmap)
        sidebar.add_page(2, pixmap)
        
        # Create ViewModel with mock plan model
        vm = PlanViewModel()
        pages = [
            PageModel(source_path="test.pdf", page_index=0, order=0),
            PageModel(source_path="test.pdf", page_index=1, order=1),
            PageModel(source_path="test.pdf", page_index=2, order=2),
        ]
        model = PlanModel(pages=pages, active_page_index=0)
        vm.set_plan_model(model)
        
        # Connect signals
        sidebar.itemClicked.connect(lambda item: vm.on_sidebar_page_clicked(
            item.data(Qt.ItemDataRole.UserRole)
        ))
        vm.page_changed.connect(sidebar.set_active_page)
        
        # Click on page 1
        item = sidebar.item(1)
        sidebar.setCurrentItem(item)
        sidebar.itemClicked.emit(item)
        
        # Verify sidebar highlights page 1
        selected = sidebar.selectedItems()
        assert len(selected) == 1
        assert selected[0].data(Qt.ItemDataRole.UserRole) == 1
        
        # Verify ViewModel page changed
        assert vm.current_page == 1


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
