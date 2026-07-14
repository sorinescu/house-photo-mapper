"""PlanViewModel - Coordinates plan pages, viewport state, and calibration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, QPointF, Signal, Slot
from PySide6.QtGui import QPixmap

from house_photo_mapper.domain.models.plan import CalibrationModel, PlanModel, PageModel
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel

if TYPE_CHECKING:
    from house_photo_mapper.domain.services.plan_renderer import PlanRenderer


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
    floor_changed = Signal(int, int)     # Emits (page_num, floor) when floor changes
    error_occurred = Signal(str)         # Emits error messages

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize PlanViewModel.

        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._plan_model: PlanModel | None = None
        self._plan_renderer: PlanRenderer | None = None
        self._current_page_index: int = -1
        self._zoom: float = 1.0
        self._rotation: int = 0
        self._initial_fit_done: bool = False

    @property
    def plan_model(self) -> PlanModel | None:
        """Get current plan model."""
        return self._plan_model

    @plan_model.setter
    def plan_model(self, model: PlanModel | None) -> None:
        """Set plan model and reset state."""
        self._plan_model = model
        self._current_page_index = -1
        self._initial_fit_done = False

        # Initialize plan renderer if model has pages
        if model and model.pages:
            self._init_plan_renderer()
            # Emit pages changed first so sidebar gets populated
            self.pages_changed.emit(self.get_sorted_pages())
            # Then set first page and generate thumbnails
            self.set_page(0)
            self.generate_all_thumbnails()
        else:
            self._plan_renderer = None
            self.pages_changed.emit([])

    def _init_plan_renderer(self) -> None:
        """Initialize plan renderer from current plan model's source path."""
        if self._plan_model is None or not self._plan_model.pages:
            return

        first_page = self._plan_model.pages[0]

        # Use original_path if available, otherwise fall back to source_path
        source_path = first_page.original_path if first_page.original_path else first_page.source_path

        # Try to find the full path
        # First check if it's an absolute path that exists
        if Path(source_path).exists():
            full_path = source_path
        else:
            # Try relative to current working directory
            cwd_path = Path.cwd() / source_path
            if cwd_path.exists():
                full_path = str(cwd_path)
            else:
                # Try to find in project directory
                # Look for the file in common locations
                for search_dir in [Path.cwd(), Path.cwd() / "plans", Path.cwd() / "assets"]:
                    candidate = search_dir / source_path
                    if candidate.exists():
                        full_path = str(candidate)
                        break
                else:
                    # Can't find the source file
                    return

        try:
            from house_photo_mapper.domain.services.plan_renderer import PlanRenderer

            self._plan_renderer = PlanRenderer(full_path)
        except Exception:
            # If renderer initialization fails, continue without rendering
            self._plan_renderer = None

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
        """Get current plan renderer."""
        return self._plan_renderer

    @plan_renderer.setter
    def plan_renderer(self, renderer: PlanRenderer | None) -> None:
        """Set plan renderer."""
        self._plan_renderer = renderer

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

        # Emit calibration_changed for the newly active page
        sorted_pages = self._plan_model.get_sorted_pages()
        if 0 <= index < len(sorted_pages):
            self.calibration_changed.emit(sorted_pages[index].calibration)

        # Render page if renderer available
        if self._plan_renderer is not None:
            page = sorted_pages[index]
            try:
                # Use 150 DPI as base rendering resolution
                pixmap = self._plan_renderer.render_page(page.page_index, dpi=150)
                self._current_pixmap = pixmap
                self.pixmap_ready.emit(pixmap)
            except Exception as e:
                self.error_occurred.emit(f"Failed to render page: {e}")

    def request_page_render(self, page_index: int) -> None:
        """Render a specific page and emit page_rendered signal.

        Uses PlanRenderer to render the page at 150 DPI and emits
        pixmap_ready with the resulting QPixmap.

        Args:
            page_index: Index in sorted page list to render.
        """
        if self._plan_model is None or self._plan_renderer is None:
            return

        sorted_pages = self._plan_model.get_sorted_pages()
        if not 0 <= page_index < len(sorted_pages):
            return

        try:
            page = sorted_pages[page_index]
            pixmap = self._plan_renderer.render_page(page.page_index, dpi=150)
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
            self._plan_renderer = renderer
            page_count = renderer.page_count()

            pages = [
                PageModel(
                    source_path=Path(pdf_path).name,
                    original_path=pdf_path,
                    page_index=i,
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
            self._plan_renderer = renderer

            page = PageModel(
                source_path=Path(image_path).name,
                original_path=image_path,
                page_index=0,
                order=0,
            )

            self._plan_model = PlanModel(pages=[page], active_page_index=0)
            self._current_page_index = 0
            self._initial_fit_done = False
            self.pages_changed.emit(self.get_sorted_pages())
            self.set_page(0)

        except Exception as e:
            self.error_occurred.emit(f"Failed to load image: {e}")

    @Slot(list)
    def on_sidebar_order_changed(self, order_list: list[dict]) -> None:
        """Handle sidebar drag-reorder and update PlanModel page order.

        Args:
            order_list: List of dicts with page_num, floor, order from sidebar.
        """
        if self._plan_model is None:
            return

        # Reorder PlanModel.pages to match sidebar order
        # Build mapping from page_num to page
        page_map = {p.page_index: p for p in self._plan_model.pages}

        # Update order field and reorder pages list
        for order_info in order_list:
            page_num = order_info["page_num"]
            order = order_info["order"]
            if page_num in page_map:
                page_map[page_num].order = order

        # Sort pages by order field
        self._plan_model.pages.sort(key=lambda p: p.order)

        # Emit signal
        self.pages_reordered.emit(self._plan_model.pages)

    @Slot(int, int)
    def on_sidebar_floor_changed(self, page_num: int, floor: int) -> None:
        """Handle floor combo change from sidebar and update PlanModel.

        Args:
            page_num: Page number (0-based source index).
            floor: New floor number (-2 to 10).
        """
        if self._plan_model is None:
            return

        # Find page by page_num (page_index)
        for page in self._plan_model.pages:
            if page.page_index == page_num:
                page.floor = floor
                self.floor_changed.emit(page_num, floor)
                break

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
        if self._plan_model is None or self._plan_renderer is None:
            return

        sorted_pages = self._plan_model.get_sorted_pages()
        for idx, page in enumerate(sorted_pages):
            # Skip first page if it's already rendered as the active page
            if idx == 0 and self._current_page_index == 0:
                continue
            try:
                # Render at lower DPI for thumbnail
                pixmap = self._plan_renderer.render_page(page.page_index, dpi=72)
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