"""MainWindow - Main application window with menus, toolbars, and central widget."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.domain.services.photo_importer import SUPPORTED_FORMATS
from house_photo_mapper.presentation.viewmodels.main_window_vm import MainWindowViewModel
from house_photo_mapper.presentation.viewmodels.photo_vm import PhotoViewModel
from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
from house_photo_mapper.presentation.views.photo_browser import PhotoBrowser
from house_photo_mapper.presentation.views.photo_metadata import PhotoMetadataPanel
from house_photo_mapper.presentation.views.plan_sidebar import PlanSidebar
from house_photo_mapper.presentation.views.plan_view import PlanView

if TYPE_CHECKING:
    from house_photo_mapper.domain.services.persistence import PersistenceService
    from house_photo_mapper.presentation.viewmodels.main_window_vm import MainWindowViewModel
    from house_photo_mapper.presentation.viewmodels.project_vm import ProjectViewModel


class MainWindow(QMainWindow):
    """Main application window.

    Connects ViewModel signals to UI updates and provides menu/toolbar actions.
    """

    def __init__(
        self,
        view_model: "MainWindowViewModel | None" = None,
        persistence: "PersistenceService | None" = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize MainWindow.

        Args:
            view_model: MainWindowViewModel instance (optional for testing).
            persistence: PersistenceService for window state (optional for testing).
            parent: Parent widget.
        """
        super().__init__(parent)

        # Create default dependencies if not provided (for testing/scaffolding)
        if view_model is None or persistence is None:
            from house_photo_mapper.domain.services.persistence import PersistenceService
            from house_photo_mapper.presentation.viewmodels.main_window_vm import (
                MainWindowViewModel,
            )

            if persistence is None:
                persistence = PersistenceService()
            if view_model is None:
                view_model = MainWindowViewModel(persistence)

        self._vm = view_model
        self._persistence = persistence

        # Create PlanViewModel and wire to ProjectViewModel
        self._plan_vm = PlanViewModel()
        self._vm.project_vm.set_plan_vm(self._plan_vm)

        # Create PhotoViewModel and wire to ProjectViewModel
        self._photo_vm = PhotoViewModel()
        self._vm.project_vm.set_photo_vm(self._photo_vm)

        self.setWindowTitle("HousePhotoMapper")
        self.resize(1200, 800)

        self._setup_ui()
        self._connect_signals()
        self._restore_state()

    def _restore_state(self) -> None:
        """Restore window geometry and state from QSettings."""
        geometry = self._persistence.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        state = self._persistence.load_window_state()
        if state:
            self.restoreState(state)

    def _setup_ui(self) -> None:
        """Set up menus, toolbars, status bar, and central widget."""
        self.setAcceptDrops(True)
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()

    def _create_menu_bar(self) -> None:
        """Create the menu bar with File, Edit, View, Window, Help menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        self._add_file_actions(file_menu)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        self._add_edit_actions(edit_menu)

        # View menu
        view_menu = menubar.addMenu("&View")
        self._add_view_actions(view_menu)

        # Window menu
        window_menu = menubar.addMenu("&Window")
        self._add_window_actions(window_menu)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        self._add_help_actions(help_menu)

    def _add_file_actions(self, menu: QMenu) -> None:
        """Add actions to File menu."""
        # New
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new project")
        new_action.triggered.connect(self._vm.new_project)
        menu.addAction(new_action)

        # Open
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self._vm.open_project)
        menu.addAction(open_action)

        # Import Plan
        import_action = QAction("Import &Plan...", self)
        import_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        import_action.setStatusTip("Import a PDF or image plan file")
        import_action.triggered.connect(self._vm.import_plan)
        menu.addAction(import_action)

        # Import Photos
        import_photos_action = QAction("Import &Photos...", self)
        import_photos_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        import_photos_action.setStatusTip("Import photos from folder")
        import_photos_action.triggered.connect(self._vm.import_photos_from_folder)
        menu.addAction(import_photos_action)

        menu.addSeparator()

        # Save
        self._save_action = QAction("&Save", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.setStatusTip("Save the current project")
        self._save_action.triggered.connect(self._vm.save_project)
        self._save_action.setEnabled(False)
        menu.addAction(self._save_action)

        # Save As
        self._save_as_action = QAction("Save &As...", self)
        self._save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._save_as_action.setStatusTip("Save the project with a new name")
        self._save_as_action.triggered.connect(self._vm.save_project_as)
        self._save_as_action.setEnabled(False)
        menu.addAction(self._save_as_action)

        menu.addSeparator()

        # Close Project
        self._close_action = QAction("&Close Project", self)
        self._close_action.setShortcut(QKeySequence("Ctrl+W"))
        self._close_action.setStatusTip("Close the current project")
        self._close_action.triggered.connect(self._close_project)
        self._close_action.setEnabled(False)
        menu.addAction(self._close_action)

        menu.addSeparator()

        # Recent projects submenu
        self._recent_menu = menu.addMenu("Recent &Projects")
        self._vm.recent_projects_changed.connect(self._update_recent_menu)

        menu.addSeparator()

        # Quit
        quit_action = QAction("E&xit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setStatusTip("Exit the application")
        app = QApplication.instance()
        if app:
            quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

    def _add_edit_actions(self, menu: QMenu) -> None:
        """Add actions to Edit menu."""
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)
        menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)
        menu.addAction(redo_action)

        menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setEnabled(False)
        menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setEnabled(False)
        menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setEnabled(False)
        menu.addAction(paste_action)

    def _add_view_actions(self, menu: QMenu) -> None:
        """Add actions to View menu."""
        toolbar_action = QAction("&Toolbar", self)
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(True)
        toolbar_action.toggled.connect(self._toggle_toolbar)
        menu.addAction(toolbar_action)

        statusbar_action = QAction("&Status Bar", self)
        statusbar_action.setCheckable(True)
        statusbar_action.setChecked(True)
        statusbar_action.toggled.connect(self._toggle_statusbar)
        menu.addAction(statusbar_action)

    def _add_window_actions(self, menu: QMenu) -> None:
        """Add actions to Window menu."""
        minimize_action = QAction("&Minimize", self)
        minimize_action.setShortcut(QKeySequence("Cmd+M"))
        minimize_action.triggered.connect(self.showMinimized)
        menu.addAction(minimize_action)

        zoom_action = QAction("&Zoom", self)
        zoom_action.triggered.connect(self._toggle_maximize)
        menu.addAction(zoom_action)

    def _add_help_actions(self, menu: QMenu) -> None:
        """Add actions to Help menu."""
        about_action = QAction("&About HousePhotoMapper", self)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)

        about_qt_action = QAction("About &Qt", self)
        def show_about_qt() -> None:
            QApplication.aboutQt()
        about_qt_action.triggered.connect(show_about_qt)
        menu.addAction(about_qt_action)

    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        self._toolbar = QToolBar("Main Toolbar", self)
        self._toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)

        self._tb_new = QAction("New", self)
        self._tb_new.triggered.connect(self._vm.new_project)
        self._toolbar.addAction(self._tb_new)

        self._tb_open = QAction("Open", self)
        self._tb_open.triggered.connect(self._vm.open_project)
        self._toolbar.addAction(self._tb_open)

        self._tb_save = QAction("Save", self)
        self._tb_save.triggered.connect(self._vm.save_project)
        self._tb_save.setEnabled(False)
        self._toolbar.addAction(self._tb_save)

        self._tb_import = QAction("Import Plan", self)
        self._tb_import.triggered.connect(self._vm.import_plan)
        self._toolbar.addAction(self._tb_import)

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _create_central_widget(self) -> None:
        """Create the central widget with PlanView, PlanSidebar, and PhotoBrowser in a splitter."""
        # Create sidebar and plan view
        self._sidebar = PlanSidebar()
        self._plan_view = PlanView(self._plan_vm)

        # Wire PlanView to PlanViewModel for calibration
        self._plan_vm.set_plan_view(self._plan_view)

        # Create photo browser and metadata panel
        self._photo_browser = PhotoBrowser()
        self._photo_metadata = PhotoMetadataPanel()

        # Create right panel for photos
        photo_panel = QWidget()
        photo_layout = QVBoxLayout(photo_panel)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        photo_layout.addWidget(self._photo_browser)
        photo_layout.addWidget(self._photo_metadata)

        # Create splitter: sidebar left, plan view center, photos right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._plan_view)
        splitter.addWidget(photo_panel)
        splitter.setStretchFactor(0, 0)  # sidebar fixed width
        splitter.setStretchFactor(1, 1)  # plan view stretches
        splitter.setStretchFactor(2, 0)  # photo panel fixed width
        self.setCentralWidget(splitter)

        # Connect sidebar signals to PlanViewModel
        self._sidebar.order_changed.connect(self._plan_vm.on_sidebar_order_changed)
        self._sidebar.floor_changed.connect(self._plan_vm.on_sidebar_floor_changed)
        self._sidebar.itemClicked.connect(self._on_sidebar_item_clicked)

        # Connect PlanViewModel signals to sidebar
        self._plan_vm.pages_changed.connect(self._on_pages_changed)
        self._plan_vm.pixmap_ready.connect(self._on_pixmap_ready)

        # Connect PhotoViewModel signals to photo browser and metadata
        self._photo_vm.photo_added.connect(self._on_photo_added)
        self._photo_vm.thumbnail_ready.connect(self._photo_browser.update_thumbnail)
        self._photo_vm.duplicates_found.connect(self._on_duplicates_found)
        self._photo_vm.metadata_changed.connect(self._photo_metadata.update_metadata)
        self._photo_browser.itemClicked.connect(self._on_photo_clicked)

    def _connect_signals(self) -> None:
        """Connect ViewModel signals to UI slots."""
        self._vm.window_title_changed.connect(self.setWindowTitle)
        self._vm.status_message_changed.connect(self._status_bar.showMessage)
        self._vm.project_vm_changed.connect(self._on_project_changed)

    @Slot(object)
    def _on_project_changed(self, project_vm: "ProjectViewModel") -> None:
        """Handle project change signal."""
        has_project = project_vm.project is not None
        self._save_action.setEnabled(has_project and project_vm.dirty)
        self._save_as_action.setEnabled(has_project)
        self._close_action.setEnabled(has_project)
        self._tb_save.setEnabled(has_project and project_vm.dirty)

    def _update_recent_menu(self, recent_projects: list[str]) -> None:
        """Update the Recent Projects submenu."""
        self._recent_menu.clear()

        if not recent_projects:
            no_recent = QAction("No recent projects", self)
            no_recent.setEnabled(False)
            self._recent_menu.addAction(no_recent)
            return

        for path in recent_projects:
            action = QAction(Path(path).name, self)
            action.setData(path)
            action.setStatusTip(path)
            action.triggered.connect(lambda checked, p=path: self._vm.open_recent_project(p))
            self._recent_menu.addAction(action)

    @Slot()
    def _show_about(self) -> None:
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About HousePhotoMapper",
            "<h3>HousePhotoMapper</h3>"
            "<p>Version 0.1.0</p>"
            "<p>Document buildings with photos and annotations.</p>"
            "<p>Built with Python, PySide6, and uv.</p>",
        )

    def _close_project(self) -> None:
        """Close the current project after prompting to save if needed."""
        # Check if there are unsaved changes
        if self._vm.project_vm and self._vm.project_vm.dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Project has unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._vm.save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # Close the project
        self._vm.project_vm.close_project()

        # Clear the sidebar and plan view
        self._sidebar.clear()

        # Reset window title
        self.setWindowTitle("HousePhotoMapper")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save window state on close."""
        self._persistence.save_window_geometry(bytes(self.saveGeometry().data()))
        self._persistence.save_window_state(bytes(self.saveState().data()))
        super().closeEvent(event)

    def _toggle_toolbar(self, visible: bool) -> None:
        """Toggle toolbar visibility."""
        self._toolbar.setVisible(visible)

    def _toggle_statusbar(self, visible: bool) -> None:
        """Toggle status bar visibility."""
        self._status_bar.setVisible(visible)

    def _toggle_maximize(self) -> None:
        """Toggle window maximized state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_sidebar_item_clicked(self, item) -> None:
        """Handle sidebar item click - switch active page."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self._plan_vm.on_sidebar_page_clicked(data["page_num"])

    def _on_pages_changed(self, pages: list) -> None:
        """Handle PlanViewModel.pages_changed signal - populate sidebar."""
        self._sidebar.clear()
        for page in pages:
            # Create a placeholder pixmap for the thumbnail
            from PySide6.QtGui import QPixmap
            placeholder = QPixmap(120, 120)
            placeholder.fill(Qt.GlobalColor.lightGray)
            self._sidebar.add_page(
                page.page_index,
                placeholder,
                page.floor,
            )

    def _on_pixmap_ready(self, pixmap) -> None:
        """Handle PlanViewModel.pixmap_ready signal - update sidebar thumbnail."""
        # Update the active page's thumbnail in the sidebar
        sorted_pages = self._plan_vm.get_sorted_pages()
        if not sorted_pages:
            return
        active_idx = self._plan_vm.current_page
        if 0 <= active_idx < len(sorted_pages):
            page = sorted_pages[active_idx]
            # Find existing item and update its icon instead of adding new
            for i in range(self._sidebar.count()):
                item = self._sidebar.item(i)
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data["page_num"] == page.page_index:
                    scaled_pixmap = pixmap.scaled(
                        120, 120,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    item.setIcon(QIcon(scaled_pixmap))
                    break

    @Slot(object)
    def _on_photo_added(self, photo) -> None:
        """Handle PhotoViewModel.photo_added signal - add photo to browser."""
        self._photo_browser.add_photo(photo.path)

    @Slot(list)
    def _on_duplicates_found(self, groups) -> None:
        """Handle PhotoViewModel.duplicates_found signal - mark duplicates in browser."""
        for group in groups:
            for path in group.photo_paths:
                self._photo_browser.mark_duplicate(path, group.group_id)

    @Slot(object)
    def _on_photo_clicked(self, item) -> None:
        """Handle photo browser item click - select photo."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._photo_vm.select_photo(path)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for shortcuts."""
        if event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self._vm.dirty:
                self._vm.save_project()
            event.accept()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self._vm.save_project_as()
            event.accept()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        """Accept drag events with supported image files."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    suffix = Path(url.toLocalFile()).suffix.lower()
                    if suffix in SUPPORTED_FORMATS:
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event) -> None:
        """Handle drop events by importing photos."""
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self._vm.import_photos(paths)
            event.acceptProposedAction()
        else:
            event.ignore()
