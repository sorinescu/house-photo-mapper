"""Tests for plan import UI: MainWindowViewModel.import_plan and menu integration."""

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestMainWindowViewModelImportPlan:
    """Unit tests for MainWindowViewModel.import_plan slot."""

    def _make_vm(self):
        """Create MainWindowViewModel with mocked dependencies."""
        from house_photo_mapper.presentation.viewmodels.main_window_vm import (
            MainWindowViewModel,
        )

        mock_persistence = MagicMock()
        mock_persistence.get_last_opened_directory.return_value = "/tmp"
        mock_project_vm = MagicMock()
        mock_plan_vm = MagicMock()
        # Configure plan_model mock for import_plans start_order calculation
        mock_plan_vm.plan_model = MagicMock()
        mock_plan_vm.plan_model.get_sorted_pages.return_value = []

        vm = MainWindowViewModel(mock_persistence)
        vm._project_vm = mock_project_vm
        mock_project_vm.plan_vm = mock_plan_vm
        return vm, mock_project_vm, mock_plan_vm, mock_persistence

    def test_import_plan_method_exists(self):
        """MainWindowViewModel has import_plan method."""
        vm, *_ = self._make_vm()
        assert callable(getattr(vm, "import_plan", None))

    def test_import_plan_shows_correct_file_dialog_filter(self):
        """import_plan shows QFileDialog with PDF and image filters."""
        vm, _, _, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = ([], "")
            vm.import_plan()
            args = mock_dialog.getOpenFileNames.call_args
            filter_arg = args[0][3] if len(args[0]) > 3 else args[1].get("filter", "")
            assert "pdf" in filter_arg.lower()
            assert "png" in filter_arg.lower()
            assert "jpg" in filter_arg.lower()

    def test_import_plan_routes_pdf_to_import_plans(self):
        """When user selects a .pdf file, import_plan calls import_plans."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.pdf"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan.pdf"], start_order=0
            )

    def test_import_plan_routes_png_to_import_plans(self):
        """When user selects a .png file, import_plan calls import_plans."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.png"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan.png"], start_order=0
            )

    def test_import_plan_routes_jpg_to_import_plans(self):
        """When user selects a .jpg file, import_plan calls import_plans."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.jpg"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan.jpg"], start_order=0
            )

    def test_import_plan_routes_jpeg_to_import_plans(self):
        """When user selects a .jpeg file, import_plan calls import_plans."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.jpeg"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan.jpeg"], start_order=0
            )

    def test_import_plan_cancel_does_nothing(self):
        """When user cancels the dialog (empty list), no load method is called."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = ([], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_not_called()

    def test_import_plan_multiple_files(self):
        """import_plan can handle multiple selected files."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (
                ["/tmp/plan1.pdf", "/tmp/plan2.pdf"],
                "",
            )
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan1.pdf", "/tmp/plan2.pdf"], start_order=0
            )

    def test_import_plan_appends_to_existing_pages(self):
        """import_plan calculates start_order from existing pages."""
        vm, _, mock_plan_vm, _ = self._make_vm()

        # Simulate existing pages with orders 0 and 1
        mock_page_0 = MagicMock()
        mock_page_0.order = 0
        mock_page_1 = MagicMock()
        mock_page_1.order = 1
        mock_plan_vm.plan_model = MagicMock()
        mock_plan_vm.plan_model.get_sorted_pages.return_value = [mock_page_0, mock_page_1]

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan3.pdf"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once_with(
                ["/tmp/plan3.pdf"], start_order=2
            )

    def test_import_plan_works_without_project(self):
        """import_plan works without a project loaded (standalone import)."""
        vm, mock_project_vm, mock_plan_vm, _ = self._make_vm()
        mock_project_vm.plan_vm = mock_plan_vm

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.pdf"], "")
            vm.import_plan()
            mock_plan_vm.import_plans.assert_called_once()

    def test_import_plan_error_emits_status_message(self):
        """error_occurred signal emits message if import_plans raises exception."""
        vm, _, mock_plan_vm, _ = self._make_vm()
        mock_plan_vm.import_plans.side_effect = RuntimeError("bad file")

        received = []
        vm.status_message_changed.connect(lambda msg: received.append(msg))

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (["/tmp/plan.pdf"], "")
            vm.import_plan()
            assert len(received) == 1
            assert "Failed to import plan" in received[0]

    def test_import_plan_sets_last_opened_directory(self):
        """import_plan updates last opened directory after successful import."""
        vm, _, mock_plan_vm, mock_persistence = self._make_vm()

        with patch(
            "house_photo_mapper.presentation.viewmodels.main_window_vm.QFileDialog"
        ) as mock_dialog:
            mock_dialog.getOpenFileNames.return_value = (
                ["/tmp/subdir/plan.pdf"],
                "",
            )
            vm.import_plan()
            mock_persistence.set_last_opened_directory.assert_called_with("/tmp/subdir")


class TestProjectViewModelPlanVmProperty:
    """Test that ProjectViewModel exposes plan_vm property."""

    def test_plan_vm_property_returns_plan_vm(self):
        """ProjectViewModel.plan_vm returns the PlanViewModel set via set_plan_vm."""
        from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel

        mock_persistence = MagicMock()
        pvm = ProjectViewModel(mock_persistence)
        mock_plan_vm = MagicMock()
        pvm.set_plan_vm(mock_plan_vm)
        assert pvm.plan_vm is mock_plan_vm

    def test_plan_vm_property_none_by_default(self):
        """ProjectViewModel.plan_vm is None when not set."""
        from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel

        mock_persistence = MagicMock()
        pvm = ProjectViewModel(mock_persistence)
        assert pvm.plan_vm is None


class TestImportPlanIntegration:
    """Integration tests: MainWindow menu action triggers VM import_plan."""

    @pytest.fixture
    def main_window(self, qapp):
        """Create MainWindow with mock ViewModel for integration testing."""
        from house_photo_mapper.presentation.views.main_window import MainWindow

        mock_vm = MagicMock()
        mock_persistence = MagicMock()
        mock_persistence.load_window_geometry.return_value = None
        mock_persistence.load_window_state.return_value = None
        window = MainWindow(view_model=mock_vm, persistence=mock_persistence)
        yield window, mock_vm
        window.close()

    def test_import_plan_action_exists_in_menu(self, main_window):
        """Import Plan action exists in the File menu."""
        window, _ = main_window
        menubar = window.menuBar()
        file_menu = None
        for action in menubar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break
        assert file_menu is not None, "File menu not found"

        import_action = None
        for action in file_menu.actions():
            if action.text() == "Import &Plan...":
                import_action = action
                break
        assert import_action is not None, "Import Plan action not found in File menu"

    def test_import_plan_action_has_shortcut(self, main_window):
        """Import Plan action has Ctrl+Shift+I shortcut."""
        window, _ = main_window
        menubar = window.menuBar()
        file_menu = None
        for action in menubar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        import_action = None
        for action in file_menu.actions():
            if action.text() == "Import &Plan...":
                import_action = action
                break

        assert import_action is not None
        shortcut = import_action.shortcut()
        assert shortcut.toString() == "Ctrl+Shift+I"

    def test_import_plan_action_triggers_vm_slot(self, main_window):
        """Clicking Import Plan action triggers import_plan on VM."""
        window, mock_vm = main_window
        menubar = window.menuBar()
        file_menu = None
        for action in menubar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        import_action = None
        for action in file_menu.actions():
            if action.text() == "Import &Plan...":
                import_action = action
                break

        assert import_action is not None
        import_action.trigger()
        mock_vm.import_plan.assert_called_once()

    def test_import_plan_action_always_enabled(self, main_window):
        """Import Plan action is always enabled (no project state dependency)."""
        window, _ = main_window
        menubar = window.menuBar()
        file_menu = None
        for action in menubar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        import_action = None
        for action in file_menu.actions():
            if action.text() == "Import &Plan...":
                import_action = action
                break

        assert import_action is not None
        assert import_action.isEnabled()
