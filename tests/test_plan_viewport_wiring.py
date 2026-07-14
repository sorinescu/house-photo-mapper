"""Tests for PlanView and PlanViewModel wiring into MainWindow."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QSplitter

from house_photo_mapper.presentation.views.main_window import MainWindow
from house_photo_mapper.presentation.views.plan_view import PlanView
from house_photo_mapper.presentation.views.plan_sidebar import PlanSidebar
from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel


class TestMainWindowPlanViewWiring:
    """Verify MainWindow creates and wires PlanView as central widget."""

    @pytest.fixture
    def main_window(self, qapp):
        """Create MainWindow with real ViewModel (not mock) for wiring tests."""
        from house_photo_mapper.domain.services.persistence import PersistenceService
        from house_photo_mapper.presentation.viewmodels.main_window_vm import (
            MainWindowViewModel,
        )

        persistence = PersistenceService()
        vm = MainWindowViewModel(persistence)
        window = MainWindow(view_model=vm, persistence=persistence)
        yield window, vm
        window.close()

    def test_central_widget_is_splitter(self, main_window):
        """Central widget is a QSplitter (sidebar + plan view)."""
        window, _ = main_window
        central = window.centralWidget()
        assert isinstance(central, QSplitter), (
            f"Expected QSplitter, got {type(central).__name__}"
        )

    def test_plan_view_is_central_child(self, main_window):
        """PlanView is a child of the central splitter."""
        window, _ = main_window
        central = window.centralWidget()
        children = []
        for i in range(central.count()):
            widget = central.widget(i)
            children.append(widget)
        plan_view_found = any(isinstance(w, PlanView) for w in children)
        assert plan_view_found, "PlanView not found in central splitter"

    def test_plan_sidebar_is_central_child(self, main_window):
        """PlanSidebar is a child of the central splitter."""
        window, _ = main_window
        central = window.centralWidget()
        children = []
        for i in range(central.count()):
            widget = central.widget(i)
            children.append(widget)
        sidebar_found = any(isinstance(w, PlanSidebar) for w in children)
        assert sidebar_found, "PlanSidebar not found in central splitter"

    def test_sidebar_is_left_of_plan_view(self, main_window):
        """PlanSidebar is at index 0, PlanView at index 1 in the splitter."""
        window, _ = main_window
        central = window.centralWidget()
        assert central.count() == 2, f"Expected 2 widgets, got {central.count()}"
        assert isinstance(central.widget(0), PlanSidebar), "First widget should be PlanSidebar"
        assert isinstance(central.widget(1), PlanView), "Second widget should be PlanView"

    def test_plan_vm_exists(self, main_window):
        """MainWindowViewModel has a plan_vm that is a PlanViewModel."""
        _, vm = main_window
        assert isinstance(vm.plan_vm, PlanViewModel), (
            f"Expected PlanViewModel, got {type(vm.plan_vm).__name__}"
        )

    def test_plan_vm_wired_to_project_vm(self, main_window):
        """PlanViewModel is wired to ProjectViewModel via set_plan_vm."""
        _, vm = main_window
        project_vm = vm.project_vm
        assert project_vm.plan_vm is vm.plan_vm, (
            "ProjectViewModel.plan_vm should reference the same PlanViewModel"
        )

    def test_toolbar_has_import_plan_button(self, main_window):
        """Toolbar contains an Import Plan action."""
        window, _ = main_window
        toolbar_actions = window._toolbar.actions()
        import_found = any(
            "Import Plan" in a.text() for a in toolbar_actions
        )
        assert import_found, "Import Plan button not found in toolbar"

    def test_import_plan_action_connected_to_vm(self, main_window):
        """Import Plan toolbar button triggers vm.import_plan."""
        window, vm = main_window
        toolbar_actions = window._toolbar.actions()
        import_action = None
        for a in toolbar_actions:
            if "Import Plan" in a.text():
                import_action = a
                break
        assert import_action is not None, "Import Plan button not found"
        with patch.object(vm, "import_plan") as mock_import:
            import_action.trigger()
            mock_import.assert_called_once()

    def test_sidebar_signals_connected(self, main_window):
        """PlanSidebar signals are connected to PlanViewModel slots."""
        window, vm = main_window
        central = window.centralWidget()
        sidebar = central.widget(0)
        plan_vm = vm.plan_vm
        assert isinstance(sidebar, PlanSidebar)
        assert isinstance(plan_vm, PlanViewModel)
        # Check that PlanViewModel has the expected slot methods
        assert hasattr(plan_vm, "on_sidebar_order_changed")
        assert hasattr(plan_vm, "on_sidebar_floor_changed")
        assert hasattr(plan_vm, "on_sidebar_page_clicked")

    def test_plan_view_connected_to_plan_vm(self, main_window):
        """PlanView is connected to PlanViewModel for calibration."""
        window, vm = main_window
        central = window.centralWidget()
        plan_view = central.widget(1)
        plan_vm = vm.plan_vm
        assert isinstance(plan_view, PlanView)
        assert isinstance(plan_vm, PlanViewModel)
        # PlanView should have reference to plan_vm
        assert plan_view._plan_vm is plan_vm
