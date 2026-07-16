"""MainWindow - Main application window with menus, toolbars, and central widget."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QIcon, QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
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
from house_photo_mapper.infrastructure.autosave import AutoSaveManager
from house_photo_mapper.infrastructure.logging import get_logger
from house_photo_mapper.infrastructure.platform import get_app_data_dir
from house_photo_mapper.infrastructure.recovery import RecoveryScanner
from house_photo_mapper.infrastructure.theme import ThemeManager, ThemeMode
from house_photo_mapper.domain.services.report_generator import ReportGeneratorService, ReportPageData
from house_photo_mapper.presentation.views.layout_dialog import LayoutDialog
from house_photo_mapper.presentation.views.recovery_dialog import RecoveryDialog
from house_photo_mapper.presentation.views.report_progress import ReportProgressDialog
from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel
from house_photo_mapper.presentation.viewmodels.main_window_vm import MainWindowViewModel
from house_photo_mapper.presentation.viewmodels.photo_vm import PhotoViewModel
from house_photo_mapper.presentation.viewmodels.plan_vm import PlanViewModel
from house_photo_mapper.presentation.viewmodels.report_vm import ReportViewModel
from house_photo_mapper.presentation.views.annotation_properties_panel import (
    AnnotationPropertiesPanel,
)
from house_photo_mapper.presentation.views.annotation_toolbar import AnnotationToolbar
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

        # Create ThemeManager
        self._theme_manager = ThemeManager(self)
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        self._theme_manager.system_theme_changed.connect(self._on_system_theme_changed)

        # Create PlanViewModel and wire to ProjectViewModel
        self._plan_vm = PlanViewModel()
        self._vm.project_vm.set_plan_vm(self._plan_vm)

        # Create PhotoViewModel and wire to ProjectViewModel
        self._photo_vm = PhotoViewModel()
        self._vm.project_vm.set_photo_vm(self._photo_vm)

        # Create AnnotationViewModel and wire to PlanViewModel
        from PySide6.QtGui import QUndoStack
        self._undo_stack = QUndoStack(self)
        self._annotation_vm = AnnotationViewModel()
        self._annotation_vm.set_undo_stack(self._undo_stack)
        self._plan_vm.set_annotation_vm(self._annotation_vm)
        self._vm.project_vm.set_annotation_vm(self._annotation_vm)

        self.setWindowTitle("HousePhotoMapper")
        self.resize(1200, 800)

        # Auto-save manager - load settings from persistence
        auto_save_enabled = self._persistence.get_auto_save_enabled()
        auto_save_interval_ms = self._persistence.get_auto_save_interval() * 1000
        self._autosave = AutoSaveManager(
            self._vm.project_vm,
            interval_ms=auto_save_interval_ms,
            parent=self,
        )
        self._autosave.enabled = auto_save_enabled
        self._autosave.save_started.connect(self._on_autosave_started)
        self._autosave.save_completed.connect(self._on_autosave_completed)

        self._setup_ui()
        self._connect_signals()
        self._restore_state()

        # Start auto-save timer if project is loaded
        self._vm.project_vm_changed.connect(self._on_project_changed_autosave)

        # Apply initial theme
        self._theme_manager.apply_theme()
        
        # Start monitoring system theme changes
        self._theme_manager.start_monitoring_system_theme()

        # Scan for crash recovery on startup
        self._scan_for_recovery()

    def _restore_state(self) -> None:
        """Restore window geometry and state from QSettings."""
        geometry = self._persistence.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        state = self._persistence.load_window_state()
        if state:
            self.restoreState(state)

    def _scan_for_recovery(self) -> None:
        """Scan for .bak files and show recovery dialog if found."""
        logger = get_logger(__name__)

        try:
            scanner = RecoveryScanner(
                app_data_dir=get_app_data_dir(),
                recent_projects=self._persistence.get_recent_projects(),
            )

            # Clean up old backups first
            scanner.cleanup_old_backups()

            # Scan for recoverable projects
            recoverable = scanner.scan_for_recoverable()

            if not recoverable:
                logger.debug("No recoverable projects found")
                return

            logger.info("Found %d recoverable project(s)", len(recoverable))

            # Show recovery dialog
            dialog = RecoveryDialog(recoverable, parent=self)
            dialog.recovery_selected.connect(self._on_recovery_selected)
            result = dialog.exec()

            # If user dismissed, delete the .bak files so they don't reappear
            from PySide6.QtWidgets import QDialog
            if result == QDialog.DialogCode.Rejected:
                for project in recoverable:
                    try:
                        project.bak_path.unlink(missing_ok=True)
                        logger.info("Deleted dismissed .bak: %s", project.bak_path)
                    except OSError as e:
                        logger.warning("Failed to delete .bak %s: %s", project.bak_path, e)

        except Exception as e:
            logger.warning("Recovery scan failed: %s", e)
            # Don't block startup on recovery scan failure

    @Slot(list)
    def _on_recovery_selected(self, bak_paths: list) -> None:
        """Handle recovery selection from dialog.

        Args:
            bak_paths: List of .bak file paths to recover.
        """
        logger = get_logger(__name__)

        for bak_path in bak_paths:
            try:
                project = self._persistence.recover_project(str(bak_path))
                # Open the recovered project
                self._vm.project_vm.load_project(project)
                logger.info("Recovered project: %s", project.project_name)
                # Only recover the first one
                break
            except Exception as e:
                logger.error("Failed to recover %s: %s", bak_path, e)
                QMessageBox.warning(
                    self,
                    "Recovery Failed",
                    f"Failed to recover project:\n{e}",
                )

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

        # Annotation menu
        annotation_menu = menubar.addMenu("&Annotation")
        self._add_annotation_actions(annotation_menu)

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
        import_photos_action.setStatusTip("Import photo files")
        import_photos_action.triggered.connect(self._vm.import_photo_files)
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

        # Export Annotations
        export_annotations_action = QAction("&Export Annotations...", self)
        export_annotations_action.setShortcut(QKeySequence("Ctrl+E"))
        export_annotations_action.setStatusTip("Export annotations as JSON")
        export_annotations_action.triggered.connect(self._vm.export_annotations)
        menu.addAction(export_annotations_action)

        # Generate Report
        self._generate_report_action = QAction("Generate &Report...", self)
        self._generate_report_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self._generate_report_action.setStatusTip("Generate a professional PDF report")
        self._generate_report_action.triggered.connect(self._generate_report)
        self._generate_report_action.setEnabled(False)
        menu.addAction(self._generate_report_action)

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
        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.setEnabled(False)
        self._undo_action.triggered.connect(self._undo_stack.undo)
        menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.setEnabled(False)
        self._redo_action.triggered.connect(self._undo_stack.redo)
        menu.addAction(self._redo_action)

        self._undo_stack.canUndoChanged.connect(self._undo_action.setEnabled)
        self._undo_stack.canRedoChanged.connect(self._redo_action.setEnabled)

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

        # Theme submenu
        menu.addSeparator()
        theme_menu = menu.addMenu("&Theme")
        
        # Light mode action
        self._light_theme_action = QAction("&Light Mode", self)
        self._light_theme_action.setShortcut(QKeySequence("Cmd+Shift+D"))
        self._light_theme_action.setStatusTip("Switch to light theme")
        self._light_theme_action.triggered.connect(lambda: self._set_theme(ThemeMode.LIGHT))
        theme_menu.addAction(self._light_theme_action)
        
        # Dark mode action
        self._dark_theme_action = QAction("&Dark Mode", self)
        self._dark_theme_action.setShortcut(QKeySequence("Cmd+Shift+D"))
        self._dark_theme_action.setStatusTip("Switch to dark theme")
        self._dark_theme_action.triggered.connect(lambda: self._set_theme(ThemeMode.DARK))
        theme_menu.addAction(self._dark_theme_action)
        
        # System theme action
        self._system_theme_action = QAction("&System", self)
        self._system_theme_action.setStatusTip("Use system theme")
        self._system_theme_action.triggered.connect(lambda: self._set_theme(ThemeMode.SYSTEM))
        theme_menu.addAction(self._system_theme_action)
        
        # Update theme action states
        self._update_theme_actions()

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

    def _add_annotation_actions(self, menu: QMenu) -> None:
        """Add actions to Annotation menu."""
        self._select_action = QAction("&Select Tool", self)
        self._select_action.setShortcut(QKeySequence("V"))
        self._select_action.setStatusTip("Select and move annotations")
        self._select_action.triggered.connect(lambda: self._annotation_vm.set_tool("select"))
        menu.addAction(self._select_action)

        self._place_marker_action = QAction("&Place Marker", self)
        self._place_marker_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self._place_marker_action.setStatusTip("Place a camera marker on the plan")
        self._place_marker_action.triggered.connect(lambda: self._annotation_vm.set_tool("place_marker"))
        menu.addAction(self._place_marker_action)

        self._draw_polygon_action = QAction("Set &Cone", self)
        self._draw_polygon_action.setStatusTip("Adjust viewing cone direction")
        self._draw_polygon_action.triggered.connect(lambda: self._annotation_vm.set_tool("set_cone"))
        menu.addAction(self._draw_polygon_action)

        menu.addSeparator()

        self._delete_action = QAction("&Delete Annotation", self)
        self._delete_action.setShortcut(QKeySequence("Delete"))
        self._delete_action.setStatusTip("Delete the selected annotation")
        self._delete_action.triggered.connect(self._delete_selected_annotation)
        self._delete_action.setEnabled(False)
        menu.addAction(self._delete_action)

    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        self._toolbar = QToolBar("Main Toolbar", self)
        self._toolbar.setObjectName("MainToolbar")
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

        self._tb_import_photos = QAction("Import Photos", self)
        self._tb_import_photos.triggered.connect(self._vm.import_photo_files)
        self._toolbar.addAction(self._tb_import_photos)

        self._tb_generate_report = QAction("Generate Report", self)
        self._tb_generate_report.triggered.connect(self._generate_report)
        self._tb_generate_report.setEnabled(False)
        self._toolbar.addAction(self._tb_generate_report)

        # Annotation toolbar
        self._annotation_toolbar = AnnotationToolbar(self)
        self._annotation_toolbar.tool_selected.connect(self._annotation_vm.set_tool)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._annotation_toolbar)

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

        # Wire PlanView to AnnotationViewModel for mouse events
        self._plan_view.set_annotation_vm(self._annotation_vm)

        # Create photo browser and metadata panel
        self._photo_browser = PhotoBrowser()
        self._photo_metadata = PhotoMetadataPanel()
        self._annotation_panel = AnnotationPropertiesPanel()
        self._annotation_panel.setVisible(False)

        # Create right panel for photos and annotation properties
        photo_panel = QWidget()
        photo_layout = QVBoxLayout(photo_panel)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        photo_layout.addWidget(self._photo_browser)
        photo_layout.addWidget(self._photo_metadata)
        photo_layout.addWidget(self._annotation_panel)

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
        self._plan_vm.thumbnail_ready.connect(self._on_plan_thumbnail_ready)

        # Connect plan_cleared signal to clear plan view
        self._vm.project_vm.plan_cleared.connect(self._on_plan_cleared)

        # Connect PhotoViewModel signals to photo browser and metadata
        self._photo_vm.photo_added.connect(self._on_photo_added)
        self._photo_vm.thumbnail_ready.connect(self._photo_browser.update_thumbnail)
        self._photo_vm.duplicates_found.connect(self._on_duplicates_found)
        self._photo_vm.metadata_changed.connect(self._photo_metadata.update_metadata)
        self._photo_browser.itemClicked.connect(self._on_photo_clicked)

        # Connect photos_cleared signal to clear photo browser
        self._vm.project_vm.photos_cleared.connect(self._on_photos_cleared)

        # Connect annotation signals
        self._annotation_vm.tool_changed.connect(self._annotation_toolbar.set_active_tool)
        self._annotation_vm.annotation_selected.connect(self._on_annotation_selected)
        self._annotation_vm.annotation_deselected.connect(self._on_annotation_deselected)
        self._annotation_vm.annotation_added.connect(self._on_annotation_added)
        self._annotation_vm.annotation_removed.connect(self._on_annotation_removed)
        self._annotation_panel.save_requested.connect(self._annotation_vm.update_annotation_metadata)
        self._annotation_panel.color_changed.connect(self._on_annotation_color_changed)
        self._annotation_panel.link_photo_requested.connect(self._on_link_photo_requested)

        # Connect photo browser ↔ annotation sync
        self._annotation_vm.annotation_selected.connect(self._highlight_photo_for_annotation)
        self._photo_vm.selection_changed.connect(self._on_photo_selection_changed)

    def _connect_signals(self) -> None:
        """Connect ViewModel signals to UI slots."""
        self._vm.window_title_changed.connect(self.setWindowTitle)
        self._vm.status_message_changed.connect(self._status_bar.showMessage)
        self._vm.project_vm_changed.connect(self._on_project_changed)

        # Auto-save: connect dirty_changed to start timer on first dirty
        self._vm.project_vm.dirty_changed.connect(self._on_dirty_changed)

    @Slot(bool)
    def _on_dirty_changed(self, dirty: bool) -> None:
        """Start auto-save timer when project becomes dirty."""
        if dirty and self._vm.project_vm.project is not None:
            if not self._autosave.is_saving:
                self._autosave.start()

    @Slot(object)
    def _on_project_changed(self, project_vm: "ProjectViewModel") -> None:
        """Handle project change signal."""
        has_project = project_vm.project is not None
        self._save_action.setEnabled(has_project)
        self._save_as_action.setEnabled(has_project)
        self._close_action.setEnabled(has_project)
        self._tb_save.setEnabled(has_project)
        self._generate_report_action.setEnabled(has_project)
        self._tb_generate_report.setEnabled(has_project)
        
        # Load theme from project settings
        if has_project:
            self._load_theme_from_project(project_vm)

    @Slot(object)
    def _on_project_changed_autosave(self, project_vm: "ProjectViewModel") -> None:
        """Start or stop auto-save based on project state."""
        has_project = project_vm.project is not None
        if has_project:
            self._autosave.start()
        else:
            self._autosave.stop()

    @Slot()
    def _on_autosave_started(self) -> None:
        """Show save indicator in status bar."""
        self._status_bar.showMessage("Auto-saving...")

    @Slot(bool, str)
    def _on_autosave_completed(self, success: bool, error_message: str) -> None:
        """Update status bar after auto-save completes."""
        if success:
            self._status_bar.showMessage("Auto-saved.", 2000)
        else:
            self._status_bar.showMessage(f"Auto-save failed: {error_message}", 5000)

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
        # Cancel any pending auto-save
        self._autosave.cancel_pending()

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
        """Save project if dirty, then save window state and exit."""
        # Cancel pending auto-save
        self._autosave.cancel_pending()

        # Save immediately if project has unsaved changes
        if self._vm.project_vm and self._vm.project_vm.dirty:
            self._status_bar.showMessage("Saving project...")
            self._vm.save_project()
            self._status_bar.showMessage("Project saved.", 2000)

        # Save window geometry and state
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

    def _set_theme(self, mode: ThemeMode) -> None:
        """Set the application theme.
        
        Args:
            mode: ThemeMode to apply.
        """
        self._theme_manager.set_theme(mode)
        self._update_theme_actions()
        self._save_theme_to_project()
    
    def _update_theme_actions(self) -> None:
        """Update theme action checked states."""
        current_mode = self._theme_manager.get_current_mode()
        self._light_theme_action.setChecked(current_mode == ThemeMode.LIGHT)
        self._dark_theme_action.setChecked(current_mode == ThemeMode.DARK)
        self._system_theme_action.setChecked(current_mode == ThemeMode.SYSTEM)
    
    @Slot(ThemeMode)
    def _on_theme_changed(self, mode: ThemeMode) -> None:
        """Handle theme change.
        
        Args:
            mode: New ThemeMode.
        """
        self._theme_manager.apply_theme()
        self._update_theme_actions()
    
    @Slot(ThemeMode)
    def _on_system_theme_changed(self, mode: ThemeMode) -> None:
        """Handle system theme change.
        
        Args:
            mode: New system ThemeMode.
        """
        # Only apply if currently using system theme
        if self._theme_manager.get_current_mode() == ThemeMode.SYSTEM:
            self._theme_manager.apply_theme()
    
    def _load_theme_from_project(self, project_vm: "ProjectViewModel") -> None:
        """Load theme preference from project settings.
        
        Args:
            project_vm: ProjectViewModel with project data.
        """
        if not project_vm.project:
            return
        
        # Get theme from UI preferences
        theme_str = project_vm.project.ui_preferences.theme.lower()
        
        # Convert string to ThemeMode
        try:
            mode = ThemeMode(theme_str)
        except ValueError:
            mode = ThemeMode.SYSTEM
        
        # Set theme without saving (we're loading)
        self._theme_manager._current_mode = mode
        self._theme_manager.apply_theme()
        self._update_theme_actions()
    
    def _save_theme_to_project(self) -> None:
        """Save current theme preference to project settings."""
        if not self._vm.project_vm.project:
            return
        
        # Update UI preferences
        self._vm.project_vm.project.ui_preferences.theme = self._theme_manager.get_current_mode().value
        self._vm.project_vm.project.mark_dirty()

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

    @Slot(int, object)
    def _on_plan_thumbnail_ready(self, page_index: int, pixmap) -> None:
        """Handle PlanViewModel.thumbnail_ready signal - update sidebar thumbnail."""
        for i in range(self._sidebar.count()):
            item = self._sidebar.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data["page_num"] == page_index:
                item.setIcon(QIcon(pixmap))
                break

    @Slot()
    def _on_plan_cleared(self) -> None:
        """Handle plan_cleared signal - clear plan view and sidebar."""
        self._plan_view.clear()
        self._sidebar.clear()

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
        """Handle photo browser item click - select photo and linked annotation."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._photo_vm.select_photo(path)
            # Check if this photo has a linked annotation
            for ann in self._annotation_vm.get_all_annotations():
                if ann.photo_path == path:
                    self._annotation_vm.select_annotation(ann.annotation_id)
                    return

    @Slot()
    def _on_photos_cleared(self) -> None:
        """Handle photos_cleared signal - clear photo browser."""
        self._photo_browser.clear()

    @Slot(str)
    def _on_annotation_selected(self, annotation_id: str) -> None:
        """Handle annotation selection - show properties panel."""
        ann = self._annotation_vm.get_annotation(annotation_id)
        if ann:
            # Resolve photo path to absolute for thumbnail
            # Use original_path from PhotoModel (handles external imports)
            photo_path = None
            if ann.photo_path:
                # Find the linked photo to get its original_path
                for p in self._photo_vm.photos:
                    if p.path == ann.photo_path:
                        if p.original_path:
                            photo_path = p.original_path
                        else:
                            # Fallback to project_dir / relative_path
                            project_dir = str(Path(self._vm.project.path).parent) if self._vm.project and self._vm.project.path else ""
                            if project_dir:
                                photo_path = str(Path(project_dir) / ann.photo_path)
                        break
            self._annotation_panel.show_annotation(
                ann.annotation_id, ann.title, ann.description, ann.tags, ann.color,
                photo_path=photo_path,
            )
            self._delete_action.setEnabled(True)
            # Enable link button if a photo is selected
            has_selection = self._photo_vm.selected_photo is not None
            self._annotation_panel.set_link_photo_enabled(has_selection)

    @Slot()
    def _on_annotation_deselected(self) -> None:
        """Handle annotation deselection - hide properties panel."""
        self._annotation_panel.clear()
        self._delete_action.setEnabled(False)
        self._annotation_panel.set_link_photo_enabled(False)

    @Slot(str)
    def _on_annotation_added(self, annotation_id: str) -> None:
        """Handle new annotation added - link to selected photo if any."""
        self._annotation_vm.select_annotation(annotation_id)
        # Link annotation to currently selected photo
        selected_photo = self._photo_vm.selected_photo
        if selected_photo:
            ann = self._annotation_vm.get_annotation(annotation_id)
            if ann:
                ann.photo_path = selected_photo.path
                selected_photo.annotation_id = annotation_id

    @Slot(str)
    def _on_annotation_removed(self, annotation_id: str) -> None:
        """Handle annotation removed - unbind from photo."""
        # Find and unbind photo that was linked to this annotation
        for photo in self._photo_vm.photos:
            if photo.annotation_id == annotation_id:
                photo.annotation_id = None
                break
        self._annotation_panel.clear()
        self._delete_action.setEnabled(False)

    @Slot(str, str)
    def _on_annotation_color_changed(self, annotation_id: str, color: str) -> None:
        """Handle annotation color change - update data model and graphics."""
        self._annotation_vm.update_annotation_color(annotation_id, color)
        # Update the graphics group color
        plan_view = self._plan_view
        if hasattr(plan_view, '_view') and hasattr(plan_view._view, '_annotation_groups'):
            group = plan_view._view._annotation_groups.get(annotation_id)
            if group:
                group.set_color(color)

    @Slot(str)
    def _on_link_photo_requested(self, annotation_id: str) -> None:
        """Link the currently selected photo to the annotation."""
        selected_photo = self._photo_vm.selected_photo
        if not selected_photo:
            return
        ann = self._annotation_vm.get_annotation(annotation_id)
        if not ann:
            return
        # Unlink previous photo if any
        if ann.photo_path:
            for photo in self._photo_vm.photos:
                if photo.path == ann.photo_path:
                    photo.annotation_id = None
                    break
        # Link new photo
        ann.photo_path = selected_photo.path
        selected_photo.annotation_id = annotation_id
        # Update thumbnail in panel - use original_path for external imports
        if selected_photo.original_path:
            photo_path = selected_photo.original_path
        else:
            project_dir = str(Path(self._vm.project.path).parent) if self._vm.project and self._vm.project.path else ""
            photo_path = str(Path(project_dir) / selected_photo.path) if project_dir else None
        if photo_path:
            self._annotation_panel.set_photo_thumbnail(photo_path)

    @Slot(object)
    def _on_photo_selection_changed(self, photo) -> None:
        """Enable/disable Link Photo button based on photo selection."""
        has_selection = photo is not None
        has_annotation = self._annotation_vm.selected_annotation_id is not None
        self._annotation_panel.set_link_photo_enabled(has_selection and has_annotation)

    @Slot(str)
    def _highlight_photo_for_annotation(self, annotation_id: str) -> None:
        """Highlight the photo in the browser that corresponds to the selected annotation."""
        ann = self._annotation_vm.get_annotation(annotation_id)
        if not ann or not ann.photo_path:
            return
        # Find and select the matching photo item in the browser
        for i in range(self._photo_browser.count()):
            item = self._photo_browser.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == ann.photo_path:
                self._photo_browser.setCurrentItem(item)
                self._photo_browser.scrollToItem(item)
                break

    def _delete_selected_annotation(self) -> None:
        """Delete the currently selected annotation."""
        from house_photo_mapper.presentation.commands import DeleteAnnotationCommand

        aid = self._annotation_vm.selected_annotation_id
        if aid:
            cmd = DeleteAnnotationCommand(
                annotation_vm=self._annotation_vm,
                annotation_id=aid,
            )
            self._undo_stack.push(cmd)

    @Slot()
    def _generate_report(self) -> None:
        """Generate a PDF report from annotations and photos."""
        annotations = self._annotation_vm.get_all_annotations()
        if not annotations:
            self._status_bar.showMessage("No annotations to report")
            return

        # Show LayoutDialog to get page format
        dialog = LayoutDialog(parent=self)
        if dialog.exec() != LayoutDialog.DialogCode.Accepted:
            return

        format_str, orientation_str = dialog.get_selected_layout()
        page_size = dialog.get_page_size_string()

        # Get project directory for resolving relative paths
        # project.path is the .hpm file path; parent is the project directory
        project_dir = str(Path(self._vm.project.path).parent) if self._vm.project and self._vm.project.path else ""
        project_path = Path(project_dir) if project_dir else None

        # Sort annotations by page_index for consistent page ordering
        sorted_annotations = sorted(annotations, key=lambda a: (a.page_index, a.annotation_id))

        # Build pages_data from annotations
        pages_data = []
        plan_vm = self._plan_vm
        photo_vm = self._photo_vm

        for ann in sorted_annotations:
            # Find linked photo
            photo = None
            for p in photo_vm.photos:
                if p.path == ann.photo_path:
                    photo = p
                    break

            # Find plan page for calibration
            # ann.page_index is the page index within the source PDF, not the position in sorted list
            plan_page = None
            if plan_vm.plan_model:
                sorted_pages = plan_vm.plan_model.get_sorted_pages()
                for p in sorted_pages:
                    if p.page_index == ann.page_index:
                        plan_page = p
                        break

            # Get calibration and resolve plan_pdf_path to absolute
            pixels_per_meter = 100.0  # default
            plan_pdf_path = ""
            plan_page_index = 0
            if plan_page:
                # Use calibration if available, otherwise use default
                if plan_page.calibration:
                    pixels_per_meter = plan_page.calibration.pixels_per_meter
                # Resolve relative path to absolute
                if project_path and plan_page.source_path:
                    plan_pdf_path = str(project_path / plan_page.source_path)
                else:
                    plan_pdf_path = plan_page.source_path
                plan_page_index = plan_page.page_index

            # Build metadata from photo EXIF
            metadata = {}
            if photo and photo.exif:
                if photo.exif.camera_make:
                    metadata["camera_make"] = photo.exif.camera_make
                if photo.exif.camera_model:
                    metadata["camera_model"] = photo.exif.camera_model
                if photo.exif.lens_model:
                    metadata["lens_model"] = photo.exif.lens_model
                if photo.exif.timestamp:
                    metadata["timestamp"] = photo.exif.timestamp.strftime(
                        "%Y-%m-%d %H:%M"
                    )

            # Get photo path - resolve to absolute
            photo_path = ""
            if photo and photo.original_path:
                # original_path is already absolute
                photo_path = photo.original_path
            elif ann.photo_path:
                # Resolve relative path to absolute
                if project_path:
                    photo_path = str(project_path / ann.photo_path)
                else:
                    photo_path = ann.photo_path

            pages_data.append(
                ReportPageData(
                    annotation_id=ann.annotation_id,
                    photo_path=photo_path,
                    plan_pdf_path=plan_pdf_path,
                    plan_page_index=plan_page_index,
                    plan_center_x=ann.position_x,
                    plan_center_y=ann.position_y,
                    plan_pixels_per_meter=pixels_per_meter,
                    direction_angle=ann.direction_angle,
                    cone_angle=ann.cone_angle,
                    color=ann.color,
                    title=ann.title or "Untitled",
                    description=ann.description,
                    metadata=metadata,
                    floor=ann.floor,
                    visible_area=ann.visible_area,
                )
            )

        # Get output path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "",
            "Report PDF (*.pdf)",
        )
        if not output_path:
            return

        # Create ViewModel and progress dialog
        project_dir = str(
            Path(self._vm.project.path).parent
        ) if self._vm.project and self._vm.project.path else "."
        self._report_vm = ReportViewModel(parent=self)
        self._report_progress_dialog = ReportProgressDialog(
            total_pages=len(pages_data), parent=self
        )

        # Connect signals
        self._report_vm.progress.connect(self._report_progress_dialog.update_progress)
        self._report_vm.finished.connect(self._on_report_finished)
        self._report_vm.error.connect(self._on_report_error)

        # Start generation
        self._report_vm.generate_report(
            pages_data=pages_data,
            output_path=output_path,
            page_size=page_size,
            project_dir=project_dir,
        )
        self._report_progress_dialog.show()

    @Slot(str)
    def _on_report_finished(self, path: str) -> None:
        """Handle report generation completion."""
        if hasattr(self, "_report_progress_dialog"):
            self._report_progress_dialog.finish()
        self._status_bar.showMessage(f"Report generated: {path}")
        # Open PDF in default viewer
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot(str)
    def _on_report_error(self, message: str) -> None:
        """Handle report generation error."""
        if hasattr(self, "_report_progress_dialog"):
            self._report_progress_dialog.finish()
        self._status_bar.showMessage(f"Report generation failed: {message}")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for shortcuts."""
        if event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._status_bar.showMessage("Saving...")
            self._vm.save_project()
            self._status_bar.showMessage("Saved.", 2000)
            event.accept()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self._vm.save_project_as()
            event.accept()
        elif event.key() == Qt.Key.Key_V and not event.modifiers():
            self._annotation_vm.set_tool("select")
            event.accept()
        elif event.key() == Qt.Key.Key_Delete:
            self._delete_selected_annotation()
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
