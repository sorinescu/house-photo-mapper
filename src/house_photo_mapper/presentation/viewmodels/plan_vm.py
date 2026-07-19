"""PlanViewModel - Coordinates plan pages, viewport state, and calibration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QPointF, Signal, Slot
from PySide6.QtGui import QPixmap

from house_photo_mapper.domain.models.plan import CalibrationModel, PlanModel, PageModel
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel

if TYPE_CHECKING:
    from house_photo_mapper.domain.services.plan_renderer import PlanRenderer
    from house_photo_mapper.presentation.viewmodels.annotation_vm import AnnotationViewModel


class PlanViewModel(QtSafeViewModel):
    """ViewModel for plan viewport: pages, zoom, rotation, calibration.

    Coordinates between PlanModel (data), PlanRenderer (rendering),
    and PlanView (display). Emits signals for UI synchronization.
    """

    # Signals for UI sync
    page_changed = Signal(int)           # Emits new page index
    pixmap_ready = Signal(QPixmap)       # Emits rendered page pixmap
    thumbnail_ready = Signal(int, QPixmap)  # Emits page_index, thumbnail pixmap
    zoom_changed = Signal(float)         # Emits zoom factor
    rotation_changed = Signal(int)       # Emits rotation angle (0, 90, 180, 270)
    calibration_changed = Signal(object) # Emits CalibrationModel or None
    pages_changed = Signal(list)         # Emits sorted page list
    pages_reordered = Signal(list)       # Emits reordered page list
    error_occurred = Signal(str)         # Emits error messages

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize PlanViewModel.

        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._plan_model: PlanModel | None = None
        self._plan_renderers: dict[str, PlanRenderer] = {}  # source_path → PlanRenderer
        self._current_page_index: int = -1
        self._zoom: float = 1.0
        self._rotation: int = 0
        self._initial_fit_done: bool = False
        self._annotation_vm: AnnotationViewModel | None = None

    @property
    def plan_model(self) -> PlanModel | None:
        """Get current plan model."""
        return self._plan_model

    def set_annotation_vm(self, vm: AnnotationViewModel) -> None:
        """Set AnnotationViewModel reference for page-change notification.

        Args:
            vm: AnnotationViewModel to notify on page changes.
        """
        self._annotation_vm = vm

    @plan_model.setter
    def plan_model(self, model: PlanModel | None) -> None:
        """Set plan model and reset state."""
        self._plan_model = model
        self._current_page_index = -1
        self._initial_fit_done = False

        # Initialize plan renderers for all source files
        if model and model.pages:
            self._init_plan_renderers()
            # Emit pages changed first so sidebar gets populated
            self.pages_changed.emit(self.get_sorted_pages())
            # Then set first page and generate thumbnails
            self.set_page(0)
            self.generate_all_thumbnails()
        else:
            self._plan_renderers.clear()
            self.pages_changed.emit([])

    def _init_plan_renderers(self) -> None:
        """Initialize plan renderers for all source files in the plan model."""
        if self._plan_model is None or not self._plan_model.pages:
            return

        from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

        # Collect unique source paths
        source_paths: set[str] = set()
        for page in self._plan_model.pages:
            source_path = page.original_path if page.original_path else page.source_path
            source_paths.add(source_path)

        # Create renderer for each unique source file
        for source_path in source_paths:
            if source_path in self._plan_renderers:
                continue  # Already have a renderer for this file

            # Try to find the full path
            full_path = self._resolve_source_path(source_path)
            if full_path is None:
                continue

            try:
                self._plan_renderers[source_path] = PlanRenderer(full_path)
            except Exception:
                # If renderer initialization fails, skip this file
                pass

    def _resolve_source_path(self, source_path: str) -> str | None:
        """Resolve a source path to a full file path.

        Args:
            source_path: Source path (absolute or relative).

        Returns:
            Full path if found, None otherwise.
        """
        # Check if it's an absolute path that exists
        if Path(source_path).exists():
            return source_path

        # Try relative to current working directory
        cwd_path = Path.cwd() / source_path
        if cwd_path.exists():
            return str(cwd_path)

        # Try to find in common locations
        for search_dir in [Path.cwd(), Path.cwd() / "plans", Path.cwd() / "assets"]:
            candidate = search_dir / source_path
            if candidate.exists():
                return str(candidate)

        return None

    def _get_renderer_for_page(self, page: PageModel) -> PlanRenderer | None:
        """Get the renderer for a specific page.

        Args:
            page: PageModel to get renderer for.

        Returns:
            PlanRenderer for the page's source file, or None.
        """
        source_path = page.original_path if page.original_path else page.source_path
        renderer = self._plan_renderers.get(source_path)
        if renderer is not None:
            return renderer

        # Try matching by renderer's own pdf_path (for legacy/test usage)
        for r in self._plan_renderers.values():
            if hasattr(r, 'pdf_path') and Path(r.pdf_path).name == Path(source_path).name:
                return r

        # Try to resolve and create renderer on demand
        full_path = self._resolve_source_path(source_path)
        if full_path is None:
            return None

        try:
            from house_photo_mapper.domain.services.plan_renderer import PlanRenderer
            renderer = PlanRenderer(full_path)
            self._plan_renderers[source_path] = renderer
            return renderer
        except Exception:
            return None

    def set_plan_model(self, model: PlanModel) -> None:
        """Set plan model and emit all UI sync signals.

        Replaces internal PlanModel reference. Emits pages_changed for sidebar,
        page_changed for active page, calibration_changed for current page.

        Args:
            model: PlanModel to set.
        """
        self._plan_model = model
        self._current_page_index = -1
        self._initial_fit_done = False

        sorted_pages = model.get_sorted_pages()
        self.pages_changed.emit(sorted_pages)

        if sorted_pages:
            self.set_page(model.active_page_index if model.active_page_index < len(sorted_pages) else 0)
        else:
            self.calibration_changed.emit(None)

    def get_plan_model(self) -> PlanModel | None:
        """Get current plan model for persistence.

        Returns:
            Current PlanModel or None if not loaded.
        """
        return self._plan_model

    @property
    def plan_renderer(self) -> PlanRenderer | None:
        """Get the renderer for the current active page."""
        if self._plan_model is None:
            return None
        active_page = self._plan_model.get_active_page()
        if active_page is None:
            return None
        return self._get_renderer_for_page(active_page)

    @plan_renderer.setter
    def plan_renderer(self, renderer: PlanRenderer | None) -> None:
        """Set plan renderer (legacy, stores for later use by page lookup)."""
        if renderer is None:
            return
        # If we have a plan model, store by first page's source path
        if self._plan_model and self._plan_model.pages:
            source_path = self._plan_model.pages[0].original_path or self._plan_model.pages[0].source_path
            self._plan_renderers[source_path] = renderer
        else:
            # Store by the renderer's own path for later lookup
            self._plan_renderers[renderer.pdf_path] = renderer

    @property
    def current_page(self) -> int:
        """Get current page index in sorted list."""
        return self._current_page_index

    @property
    def current_pixmap(self) -> QPixmap | None:
        """Get current page pixmap (cached from last render)."""
        return self._current_pixmap if hasattr(self, '_current_pixmap') else None

    @property
    def zoom(self) -> float:
        """Get current zoom factor."""
        return self._zoom

    @property
    def rotation(self) -> int:
        """Get current rotation angle."""
        return self._rotation

    @property
    def calibration(self) -> CalibrationModel | None:
        """Get calibration for current active page."""
        if self._plan_model is None:
            return None
        active_page = self._plan_model.get_active_page()
        if active_page is None:
            return None
        return active_page.calibration

    def get_sorted_pages(self) -> list[PageModel]:
        """Get pages sorted by display order."""
        if self._plan_model is None:
            return []
        return self._plan_model.get_sorted_pages()

    @Slot(int)
    def set_page(self, index: int) -> None:
        """Set active page by index in sorted list and render it.

        Args:
            index: Index in sorted page list.
        """
        if self._plan_model is None:
            self.error_occurred.emit("No plan model loaded")
            return

        sorted_pages = self._plan_model.get_sorted_pages()
        if not 0 <= index < len(sorted_pages):
            self.error_occurred.emit(f"Page index {index} out of range [0, {len(sorted_pages)})")
            return

        self._plan_model.set_active_page(index)
        self._current_page_index = index
        self._initial_fit_done = False
        self.page_changed.emit(index)

        # Render page if renderer available — clear scene BEFORE creating annotations
        renderer = self._get_renderer_for_page(sorted_pages[index])
        if renderer is not None:
            page = sorted_pages[index]
            try:
                pixmap = renderer.render_page(page.source_page_index, dpi=150)
                self._current_pixmap = pixmap
                self.pixmap_ready.emit(pixmap)
            except Exception as e:
                self.error_occurred.emit(f"Failed to render page: {e}")

        # Notify annotation VM of page change (after scene is cleared)
        if self._annotation_vm is not None:
            sorted_pages = self._plan_model.get_sorted_pages()
            if 0 <= index < len(sorted_pages):
                self._annotation_vm.set_current_page(sorted_pages[index].page_index)

        # Emit calibration_changed for the newly active page
        sorted_pages = self._plan_model.get_sorted_pages()
        if 0 <= index < len(sorted_pages):
            self.calibration_changed.emit(sorted_pages[index].calibration)

    def request_page_render(self, page_index: int) -> None:
        """Render a specific page and emit page_rendered signal.

        Uses PlanRenderer to render the page at 150 DPI and emits
        pixmap_ready with the resulting QPixmap.

        Args:
            page_index: Index in sorted page list to render.
        """
        if self._plan_model is None:
            return

        sorted_pages = self._plan_model.get_sorted_pages()
        if not 0 <= page_index < len(sorted_pages):
            return

        renderer = self._get_renderer_for_page(sorted_pages[page_index])
        if renderer is None:
            return

        try:
            page = sorted_pages[page_index]
            pixmap = renderer.render_page(page.page_index, dpi=150)
            self._current_pixmap = pixmap
            self.pixmap_ready.emit(pixmap)
        except Exception as e:
            self.error_occurred.emit(f"Failed to render page: {e}")

    @Slot(float)
    def set_zoom(self, factor: float) -> None:
        """Set zoom factor and emit signal.

        Args:
            factor: Zoom factor (1.0 = 100%).
        """
        if factor <= 0:
            return
        self._zoom = factor
        self.zoom_changed.emit(factor)

    ZOOM_STEP = 1.15

    def zoom_in(self) -> None:
        """Zoom in by one step."""
        self.set_zoom(self._zoom * self.ZOOM_STEP)

    def zoom_out(self) -> None:
        """Zoom out by one step."""
        self.set_zoom(self._zoom / self.ZOOM_STEP)

    def fit_to_window(self) -> None:
        """Fit the plan to the viewport (emits zoom_changed with factor 0 as sentinel)."""
        self._zoom = 0.0
        self.zoom_changed.emit(0.0)

    @Slot(int)
    def set_rotation(self, angle: int) -> None:
        """Set rotation angle and emit signal.

        Args:
            angle: Rotation in degrees (0, 90, 180, 270).
        """
        # Normalize to 0-270
        angle = angle % 360
        if angle not in (0, 90, 180, 270):
            angle = (angle // 90) * 90
        self._rotation = angle
        self.rotation_changed.emit(angle)

    @Slot()
    def rotate_cw(self) -> None:
        """Rotate 90° clockwise."""
        self.set_rotation((self._rotation + 90) % 360)

    @Slot()
    def rotate_ccw(self) -> None:
        """Rotate 90° counter-clockwise."""
        self.set_rotation((self._rotation - 90) % 360)

    def get_scene_transform(self) -> tuple[float, QPointF]:
        """Get current scene transform for calibration storage.

        Returns:
            Tuple of (scale_factor, scene_origin_in_view_coords).
        """
        return self._zoom, QPointF(0, 0)

    def set_calibration(self, calibration: CalibrationModel) -> None:
        """Set calibration for current active page.

        Args:
            calibration: CalibrationModel to store.
        """
        if self._plan_model is None:
            return
        active_page = self._plan_model.get_active_page()
        if active_page is not None:
            active_page.calibration = calibration
            self.calibration_changed.emit(calibration)

    def clear_calibration(self) -> None:
        """Clear calibration for current active page."""
        if self._plan_model is None:
            return
        active_page = self._plan_model.get_active_page()
        if active_page is not None:
            active_page.calibration = None
            self.calibration_changed.emit(None)

    @Slot()
    def start_calibration(self) -> None:
        """Open calibration dialog for current page.

        Creates CalibrationViewModel and CalibrationDialog, connects
        calibration_ready to set_calibration, and shows the dialog.
        The dialog installs an event filter on PlanGraphicsView for
        click capture in scene coordinates.
        """
        from house_photo_mapper.presentation.viewmodels.calibration_vm import CalibrationViewModel
        from house_photo_mapper.presentation.views.calibration_dialog import CalibrationDialog

        cal_vm = CalibrationViewModel(parent=self)

        # Get plan view for click capture (if available)
        plan_view = getattr(self, "_plan_view", None)

        dialog = CalibrationDialog(cal_vm, plan_view=plan_view)
        cal_vm.calibration_ready.connect(self.set_calibration)
        dialog.exec()

    def set_plan_view(self, plan_view) -> None:
        """Set the PlanView reference for calibration click capture.

        Args:
            plan_view: PlanView instance (or None to clear).
        """
        self._plan_view = plan_view

    def load_plan_from_pdf(self, pdf_path: str) -> None:
        """Load a PDF plan and create PlanModel with pages.

        Args:
            pdf_path: Path to PDF file.
        """
        from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

        try:
            renderer = PlanRenderer(pdf_path)
            source_path = Path(pdf_path).name

            # Store renderer
            self._plan_renderers[pdf_path] = renderer

            page_count = renderer.page_count()

            pages = [
                PageModel(
                    source_path=source_path,
                    original_path=pdf_path,
                    page_index=i,
                    source_page_index=i,
                    order=i,
                )
                for i in range(page_count)
            ]

            self._plan_model = PlanModel(pages=pages, active_page_index=0)
            self._current_page_index = 0
            self._initial_fit_done = False
            self.pages_changed.emit(self.get_sorted_pages())
            self.set_page(0)

        except Exception as e:
            self.error_occurred.emit(f"Failed to load PDF: {e}")

    def load_plan_from_image(self, image_path: str) -> None:
        """Load an image plan (PNG/JPG/TIFF).

        Args:
            image_path: Path to image file.
        """
        from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

        try:
            renderer = PlanRenderer(image_path)
            source_path = Path(image_path).name

            # Store renderer
            self._plan_renderers[image_path] = renderer

            page = PageModel(
                source_path=source_path,
                original_path=image_path,
                page_index=0,
                source_page_index=0,
                order=0,
            )

            self._plan_model = PlanModel(pages=[page], active_page_index=0)
            self._current_page_index = 0
            self._initial_fit_done = False
            self.pages_changed.emit(self.get_sorted_pages())
            self.set_page(0)

        except Exception as e:
            self.error_occurred.emit(f"Failed to load image: {e}")

    def import_plans(self, paths: list[str], start_order: int = 0) -> None:
        """Import one or more plan files, appending pages to existing model.

        Pages from all files are added with sequential auto-generated names
        ("Page {idx}") and order starting from start_order. page_index is
        globally unique across all imported files.

        Args:
            paths: List of file paths to import (PDF or images).
            start_order: Starting order value for new pages.
        """
        from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

        if not paths:
            return

        # Calculate starting page_index from existing pages
        next_page_index = 0
        if self._plan_model is not None:
            for p in self._plan_model.pages:
                if p.page_index >= next_page_index:
                    next_page_index = p.page_index + 1

        new_pages: list[PageModel] = []
        order_counter = start_order

        for path in paths:
            suffix = Path(path).suffix.lower()
            if suffix == ".pdf":
                try:
                    renderer = PlanRenderer(path)
                    source_path = Path(path).name
                    self._plan_renderers[path] = renderer
                    page_count = renderer.page_count()

                    for i in range(page_count):
                        new_pages.append(PageModel(
                            source_path=source_path,
                            original_path=path,
                            page_index=next_page_index,
                            source_page_index=i,
                            order=order_counter,
                            name=f"Page {order_counter + 1}",
                        ))
                        next_page_index += 1
                        order_counter += 1
                except Exception as e:
                    self.error_occurred.emit(f"Failed to load PDF {Path(path).name}: {e}")

            elif suffix in (".png", ".jpg", ".jpeg"):
                try:
                    renderer = PlanRenderer(path)
                    source_path = Path(path).name
                    self._plan_renderers[path] = renderer

                    new_pages.append(PageModel(
                        source_path=source_path,
                        original_path=path,
                        page_index=next_page_index,
                        source_page_index=0,
                        order=order_counter,
                        name=f"Page {order_counter + 1}",
                    ))
                    next_page_index += 1
                    order_counter += 1
                except Exception as e:
                    self.error_occurred.emit(f"Failed to load image {Path(path).name}: {e}")
            else:
                self.error_occurred.emit(f"Unsupported file type: {suffix}")

        if not new_pages:
            return

        # Append to existing model or create new
        if self._plan_model is not None:
            self._plan_model.pages.extend(new_pages)
        else:
            self._plan_model = PlanModel(pages=new_pages, active_page_index=0)

        self.pages_changed.emit(self.get_sorted_pages())

        # Set to first page if this is the first import
        if self._current_page_index < 0:
            self.set_page(0)

    @Slot(int)
    def delete_page(self, page_num: int) -> None:
        """Delete a page by its page_num (page_index in source document).

        Removes the page from the model, reorders remaining pages, and
        emits pages_changed. If the deleted page was active, switches to
        the first available page.

        Args:
            page_num: Page number (page_index) to delete.
        """
        if self._plan_model is None:
            return

        # Find and remove the page
        page_to_delete = None
        for page in self._plan_model.pages:
            if page.page_index == page_num:
                page_to_delete = page
                break

        if page_to_delete is None:
            return

        self._plan_model.pages.remove(page_to_delete)

        # Reorder remaining pages
        for i, page in enumerate(sorted(self._plan_model.pages, key=lambda p: p.order)):
            page.order = i

        # Check if we deleted the active page
        sorted_pages = self._plan_model.get_sorted_pages()
        if not sorted_pages:
            self._current_page_index = -1
            self.pages_changed.emit([])
            self.calibration_changed.emit(None)
            return

        # Adjust active_page_index if needed
        if self._plan_model.active_page_index >= len(sorted_pages):
            self._plan_model.active_page_index = len(sorted_pages) - 1

        self.pages_changed.emit(sorted_pages)
        self.set_page(self._plan_model.active_page_index)

    @Slot(int, str)
    def rename_page(self, page_num: int, name: str) -> None:
        """Rename a page.

        Args:
            page_num: Page number (page_index) to rename.
            name: New name for the page.
        """
        if self._plan_model is None:
            return

        for page in self._plan_model.pages:
            if page.page_index == page_num:
                page.name = name
                # Emit pages_changed so sidebar updates the display
                self.pages_changed.emit(self.get_sorted_pages())
                break

    @Slot(list)
    def on_sidebar_order_changed(self, order_list: list[dict]) -> None:
        """Handle sidebar drag-reorder and update PlanModel page order.

        Args:
            order_list: List of dicts with page_num, order from sidebar.
        """
        if self._plan_model is None:
            return

        # Reorder PlanModel.pages to match sidebar order
        # Build mapping from page_num to page
        page_map = {p.page_index: p for p in self._plan_model.pages}

        # Update order field
        for order_info in order_list:
            page_num = order_info["page_num"]
            order = order_info["order"]
            if page_num in page_map:
                page_map[page_num].order = order

        # Sort pages by order field
        self._plan_model.pages.sort(key=lambda p: p.order)

        # Emit signal
        self.pages_reordered.emit(self._plan_model.pages)

    @Slot(int)
    def on_sidebar_page_clicked(self, page_num: int) -> None:
        """Handle page click from sidebar and switch active page.

        Args:
            page_num: Page number (0-based source index) clicked in sidebar.
        """
        if self._plan_model is None:
            return

        # Find the index in sorted pages list
        sorted_pages = self._plan_model.get_sorted_pages()
        for idx, page in enumerate(sorted_pages):
            if page.page_index == page_num:
                self.set_page(idx)
                break

    @property
    def pages(self) -> list[PageModel]:
        """Get pages property for sidebar initial population.

        Returns:
            List of PageModel sorted by display order.
        """
        if self._plan_model is None:
            return []
        return self._plan_model.get_sorted_pages()

    def generate_all_thumbnails(self) -> None:
        """Generate thumbnails for all pages in the plan.

        Uses a smaller size for sidebar thumbnails (120x120).
        Emits thumbnail_ready for each page as it completes.
        Skips the first page if it's already the active page.
        """
        if self._plan_model is None:
            return

        sorted_pages = self._plan_model.get_sorted_pages()
        for idx, page in enumerate(sorted_pages):
            # Skip first page if it's already rendered as the active page
            if idx == 0 and self._current_page_index == 0:
                continue

            renderer = self._get_renderer_for_page(page)
            if renderer is None:
                continue

            try:
                # Render at lower DPI for thumbnail
                pixmap = renderer.render_page(page.source_page_index, dpi=72)
                # Scale to thumbnail size
                from PySide6.QtCore import Qt
                scaled = pixmap.scaled(
                    120, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_ready.emit(page.page_index, scaled)
            except Exception:
                # Skip failed thumbnails - placeholder will remain
                pass


if __name__ == "__main__":
    # Quick manual test
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    vm = PlanViewModel()
    print("PlanViewModel created successfully")
    print(f"Signals: page_changed, pixmap_ready, zoom_changed, rotation_changed, calibration_changed")
