# Phase 6: Report Generation - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 10
**Analogs found:** 10 / 10

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/house_photo_mapper/domain/services/report_generator.py` | service | file-I/O | `src/house_photo_mapper/domain/services/tile_pyramid.py` | role-match |
| `src/house_photo_mapper/domain/services/plan_snippet.py` | service | transform | `src/house_photo_mapper/domain/services/plan_renderer.py` | exact |
| `src/house_photo_mapper/domain/services/camera_overlay.py` | service | transform | `src/house_photo_mapper/domain/services/calibration.py` | role-match |
| `src/house_photo_mapper/presentation/viewmodels/report_vm.py` | viewmodel | event-driven | `src/house_photo_mapper/presentation/viewmodels/calibration_vm.py` | exact |
| `src/house_photo_mapper/presentation/views/layout_dialog.py` | view | request-response | `src/house_photo_mapper/presentation/views/calibration_dialog.py` | exact |
| `src/house_photo_mapper/presentation/views/report_progress.py` | view | event-driven | `src/house_photo_mapper/presentation/views/recovery_dialog.py` | role-match |
| `tests/test_report_generator.py` | test | integration | `tests/test_calibration.py` | exact |
| `tests/test_plan_snippet.py` | test | unit | `tests/test_tile_pyramid.py` | exact |
| `tests/test_camera_overlay.py` | test | unit | `tests/test_calibration.py` | role-match |
| `tests/test_layout_dialog.py` | test | unit | `tests/test_calibration.py` | role-match |

## Pattern Assignments

### `src/house_photo_mapper/domain/services/report_generator.py` (service, file-I/O)

**Analog:** `src/house_photo_mapper/domain/services/tile_pyramid.py`

**Imports pattern** (lines 1-10):
```python
"""ReportGenerator: PDF report generation with background processing via ProcessPoolExecutor."""

from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import fitz  # PyMuPDF
import logging

log = logging.getLogger(__name__)
```

**Background processing pattern** (lines 40-70):
```python
def render_page_worker(args: tuple) -> bytes:
    """Worker function to render a single report page in a separate process.
    
    Opens its own document handle (PyMuPDF is not thread-safe).
    Returns PNG bytes for efficient caching.
    
    Args:
        args: Tuple of (pdf_path, page_data_dict).
    
    Returns:
        PNG bytes of the rendered page.
    """
    doc = fitz.open(pdf_path)
    try:
        # ... render logic
        return pix.tobytes("png")
    finally:
        doc.close()
        fitz.TOOLS.store_shrink(100)
```

**Resource management pattern** (lines 176-188):
```python
def shutdown(self) -> None:
    """Shutdown executor and release resources."""
    self._executor.shutdown(wait=True)
    self._cache.clear()
    self._futures.clear()
    log.debug("TilePyramid shutdown complete")

def __enter__(self) -> "TilePyramid":
    return self

def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self.shutdown()
```

**Key adaptation:** Use `ProcessPoolExecutor` with `max_tasks_per_child=50` for PDF generation workers. Pass only primitive data (strings, numbers, lists, dicts) to workers to avoid pickle errors.

---

### `src/house_photo_mapper/domain/services/plan_snippet.py` (service, transform)

**Analog:** `src/house_photo_mapper/domain/services/plan_renderer.py`

**Imports pattern** (lines 1-10):
```python
"""PlanSnippet: PyMuPDF plan region rendering for report generation."""

import fitz  # PyMuPDF
from PIL import Image, ImageOps
from pathlib import Path
from typing import Dict, Optional
import logging

log = logging.getLogger(__name__)
```

**PyMuPDF rendering pattern** (lines 48-69):
```python
def render_page(self, page_num: int, dpi: float = 150) -> QPixmap:
    """Render a PDF page to QPixmap at specified DPI.
    
    Args:
        page_num: Page index in document.
        dpi: Target DPI (default 150). PDF base is 72 DPI.
    
    Returns:
        QPixmap with rendered page content.
    """
    dlist = self.get_display_list(page_num)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = dlist.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)
    
    # Zero-copy QImage from pixmap samples
    fmt = QImage.Format.Format_RGB888
    qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
    # CRITICAL: Keep pixmap alive while QImage references its buffer
    qimg._pymupdf_pixmap = pix
    
    return QPixmap.fromImage(qimg)
```

**Clip rectangle pattern** (lines 71-92):
```python
def render_tile(
    self, page_num: int, dpi: float, clip_rect: fitz.Rect
) -> QPixmap:
    """Render a tile region of a PDF page for tile pyramid.
    
    Args:
        page_num: Page index in document.
        dpi: Target DPI for this tile level.
        clip_rect: Rectangle in page points to render.
    
    Returns:
        QPixmap with tile content.
    """
    dlist = self.get_display_list(page_num)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = dlist.get_pixmap(matrix=mat, clip=clip_rect, alpha=False, colorspace=fitz.csRGB)
    
    fmt = QImage.Format.Format_RGB888
    qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
    qimg._pymupdf_pixmap = pix
    return QPixmap.fromImage(qimg)
```

**Key adaptation:** Use `page.get_pixmap(matrix=mat, clip=clip, alpha=False)` to extract plan region. Convert scene coordinates to PDF points using `center_x / pixels_per_meter * 72`. Clamp clip to page bounds with `clip & page.rect`.

---

### `src/house_photo_mapper/domain/services/camera_overlay.py` (service, transform)

**Analog:** `src/house_photo_mapper/domain/services/calibration.py`

**Imports pattern** (lines 1-15):
```python
"""CameraOverlay: Camera symbol and viewing cone drawing math."""

from __future__ import annotations

import math
from typing import Tuple

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
```

**Math/geometry service pattern** (lines 17-62):
```python
class CameraOverlay:
    """Stateless service for computing camera symbol and viewing cone geometry.
    
    All methods are static — no state is held between calls. Overlay
    operates entirely in PDF point coordinates.
    """
    
    @staticmethod
    def compute_cone_vertices(
        center_x: float,
        center_y: float,
        direction_angle: float,
        cone_angle: float,
        cone_length: float,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Compute left and right vertices of viewing cone triangle.
        
        Args:
            center_x: Camera X position in PDF points.
            center_y: Camera Y position in PDF points.
            direction_angle: Viewing direction in degrees (0=right, CCW).
            cone_angle: Cone spread angle in degrees.
            cone_length: Length of cone in PDF points.
        
        Returns:
            Tuple of (left_vertex, right_vertex) as (x, y) tuples.
        
        Raises:
            ValueError: If cone_angle <= 0 or cone_length <= 0.
        """
        if cone_angle <= 0:
            raise ValueError("cone_angle must be > 0")
        if cone_length <= 0:
            raise ValueError("cone_length must be > 0")
        
        rad = math.radians(direction_angle)
        half_cone = math.radians(cone_angle / 2)
        
        left_rad = rad + half_cone
        right_rad = rad - half_cone
        
        left = (
            center_x + cone_length * math.cos(left_rad),
            center_y + cone_length * math.sin(left_rad),
        )
        right = (
            center_x + cone_length * math.cos(right_rad),
            center_y + cone_length * math.sin(right_rad),
        )
        
        return left, right
```

**Validation pattern** (lines 44-52):
```python
if cone_angle <= 0:
    raise ValueError("cone_angle must be > 0")
if cone_length <= 0:
    raise ValueError("cone_length must be > 0")
```

**Key adaptation:** Separate math/geometry computation from drawing. Provide `draw_camera_overlay()` function that takes a `canvas.Canvas` and uses `canvas.circle()`, `canvas.line()`, `canvas.setFillColor()`, etc.

---

### `src/house_photo_mapper/presentation/viewmodels/report_vm.py` (viewmodel, event-driven)

**Analog:** `src/house_photo_mapper/presentation/viewmodels/calibration_vm.py`

**Imports pattern** (lines 1-20):
```python
"""ReportViewModel: Manages report generation state and progress."""

from __future__ import annotations

from enum import IntEnum, auto

from PySide6.QtCore import Signal, Slot

from house_photo_mapper.domain.services.report_generator import ReportGeneratorService
from house_photo_mapper.infrastructure.qt_patterns import QtSafeViewModel
```

**ViewModel signal pattern** (lines 40-68):
```python
class ReportViewModel(QtSafeViewModel):
    """ViewModel for report generation dialog.
    
    Manages generation state, progress, and cancellation. Emits signals for UI updates.
    """
    
    # Signals
    progress = Signal(int, int)          # (current, total)
    finished = Signal(str)               # output file path
    error = Signal(str)                  # error message
    cancelled = Signal()                 # generation cancelled
    
    def __init__(self, parent=None) -> None:
        """Initialize ReportViewModel.
        
        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._current = 0
        self._total = 0
        self._cancelled = False
        self._output_path = ""
```

**Slot pattern** (lines 95-113):
```python
@Slot(float, str)
def set_known_distance(self, distance: float, unit: str = "meters") -> None:
    """Set known distance with unit conversion.
    
    Args:
        distance: Known real-world distance.
        unit: Unit of measurement ("meters", "feet", "inches").
    """
    if distance <= 0:
        self.error_message.emit("Distance must be greater than zero")
        return
    
    conversion = UNIT_TO_METERS.get(unit)
    if conversion is None:
        self.error_message.emit(f"Unknown unit: {unit}")
        return
    
    self._known_distance_m = distance * conversion
    self._set_step(CalibrationStep.POINT1)
```

**Key adaptation:** Use `QThread`-based worker for background generation. Emit `progress` signal with `(current, total)` for UI updates. Support cancellation via `_cancelled` flag.

---

### `src/house_photo_mapper/presentation/views/layout_dialog.py` (view, request-response)

**Analog:** `src/house_photo_mapper/presentation/views/calibration_dialog.py`

**Imports pattern** (lines 1-40):
```python
"""LayoutDialog: A4/Letter/Portrait/Landscape selection for report generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
)

from house_photo_mapper.presentation.viewmodels.report_vm import ReportViewModel

if TYPE_CHECKING:
    pass
```

**Dialog setup pattern** (lines 42-117):
```python
class LayoutDialog(QDialog):
    """Dialog for selecting report layout options.
    
    Allows user to choose page format (A4, Letter) and orientation (Portrait, Landscape).
    """
    
    def __init__(
        self,
        vm: ReportViewModel,
        parent=None,
    ) -> None:
        """Initialize LayoutDialog.
        
        Args:
            vm: ReportViewModel to bind to.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._vm = vm
        
        self.setWindowTitle("Report Layout")
        self.setMinimumWidth(350)
        self.setMinimumHeight(250)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Page format group
        format_group = QGroupBox("Page Format")
        format_layout = QFormLayout()
        
        self._format_combo = QComboBox()
        self._format_combo.addItems(["A4", "US Letter"])
        format_layout.addRow("Format:", self._format_combo)
        
        self._orientation_combo = QComboBox()
        self._orientation_combo.addItems(["Portrait", "Landscape"])
        format_layout.addRow("Orientation:", self._orientation_combo)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)
        
        button_layout.addStretch()
        
        self._ok_btn = QPushButton("OK")
        self._ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self._ok_btn)
        
        layout.addLayout(button_layout)
```

**Signal connection pattern** (lines 219-224):
```python
def _connect_signals(self) -> None:
    """Connect ViewModel signals to UI updates."""
    self._vm.step_changed.connect(self._on_step_changed)
    self._vm.calibration_ready.connect(self._on_calibration_ready)
    self._vm.cancelled.connect(self._on_cancelled)
    self._vm.error_message.connect(self._on_error)
```

**Key adaptation:** Simple dialog with `QComboBox` for page format and orientation. Return selected values via `accept()` with result stored in ViewModel.

---

### `src/house_photo_mapper/presentation/views/report_progress.py` (view, event-driven)

**Analog:** `src/house_photo_mapper/presentation/views/recovery_dialog.py`

**Imports pattern** (lines 1-30):
```python
"""ReportProgressDialog: Shows progress during report generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QWidget,
)

if TYPE_CHECKING:
    from house_photo_mapper.presentation.viewmodels.report_vm import ReportViewModel

logger = logging.getLogger(__name__)
```

**Dialog with signals pattern** (lines 33-66):
```python
class RecoveryDialog(QDialog):
    """Dialog for selecting and recovering projects from .bak files.
    
    Displays a table of recoverable projects with timestamps and preview data.
    Allows the user to select one or more projects to recover, or dismiss.
    
    Signals:
        recovery_selected: Emitted with list of bak_path objects to recover.
    """
    
    recovery_selected = Signal(list)  # list[Path]
    
    def __init__(
        self,
        recoverable_projects: list[RecoverableProject],
        parent: QWidget | None = None,
    ) -> None:
        """Initialize RecoveryDialog.
        
        Args:
            recoverable_projects: List of RecoverableProject instances to show.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._projects = recoverable_projects
        self._selected_indices: list[int] = []
        
        self.setWindowTitle("Crash Recovery")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._populate_table()
```

**Progress bar pattern** (lines 67-109):
```python
def _setup_ui(self) -> None:
    """Set up the dialog layout."""
    layout = QVBoxLayout(self)
    
    # Header
    header = QLabel(
        f"Found {len(self._projects)} recoverable project(s):"
    )
    header.setStyleSheet("font-weight: bold; font-size: 14px;")
    layout.addWidget(header)
    
    description = QLabel(
        "These projects were saved recently before the application closed. "
        "Select one or more to recover, or dismiss to start fresh."
    )
    description.setWordWrap(True)
    layout.addWidget(description)
    
    # Project table
    self._table = QTableWidget()
    self._table.setColumnCount(5)
    self._table.setHorizontalHeaderLabels([
        "Project",
        "Modified",
        "Photos",
        "Annotations",
        "Plans",
    ])
```

**Key adaptation:** Use `QProgressBar` for progress display. Connect to ViewModel's `progress` signal. Include Cancel button that calls `vm.cancel()`.

---

### `tests/test_report_generator.py` (test, integration)

**Analog:** `tests/test_calibration.py`

**Imports pattern** (lines 1-15):
```python
"""Tests for ReportGeneratorService."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from house_photo_mapper.domain.services.report_generator import ReportGeneratorService
```

**Test class pattern** (lines 24-40):
```python
class TestCalibrationService:
    """Tests for CalibrationService calibrate() and verify() methods."""
    
    def test_calibrate_basic(self, qapp):
        """Test calibrate computes correct ppm from two points and known distance."""
        p1 = QPointF(0.0, 0.0)
        p2 = QPointF(100.0, 0.0)  # 100 pixels apart
        known_m = 1.0  # 1 meter
        
        cal = CalibrationService.calibrate(p1, p2, known_m)
        
        assert cal.pixels_per_meter == pytest.approx(100.0)
        assert cal.verified is False
        assert cal.reference_distance_m == pytest.approx(1.0)
```

**Key adaptation:** Use `qapp` fixture for Qt integration tests. Test PDF generation with temporary files. Mock PyMuPDF operations for unit tests.

---

### `tests/test_plan_snippet.py` (test, unit)

**Analog:** `tests/test_tile_pyramid.py`

**Imports pattern** (lines 1-15):
```python
"""Tests for PlanSnippet."""

import pytest
from pathlib import Path
import tempfile
import fitz

from house_photo_mapper.domain.services.plan_snippet import (
    PlanSnippet,
    extract_plan_snippet,
)
```

**Test class pattern** (lines 17-47):
```python
class TestTileSpec:
    """Tests for TileSpec dataclass."""
    
    def test_tile_spec_creation(self):
        """Test TileSpec creation with all fields."""
        spec = TileSpec(page_num=0, level=1, tile_x=2, tile_y=3, dpi=150)
        assert spec.page_num == 0
        assert spec.level == 1
        assert spec.tile_x == 2
        assert spec.tile_y == 3
        assert spec.dpi == 150
    
    def test_tile_spec_hashable(self):
        """Test TileSpec can be used as dict key."""
        spec1 = TileSpec(page_num=0, level=1, tile_x=0, tile_y=0, dpi=150)
        spec2 = TileSpec(page_num=0, level=1, tile_x=0, tile_y=0, dpi=150)
        spec3 = TileSpec(page_num=0, level=2, tile_x=0, tile_y=0, dpi=300)
        
        cache = {spec1: "tile_data"}
        assert spec2 in cache  # Equal specs should have same hash
        assert spec3 not in cache  # Different level should have different hash
```

**Key adaptation:** Use temporary PDF files for testing. Verify PNG bytes output. Test coordinate conversion from scene to PDF points.

---

### `tests/test_camera_overlay.py` (test, unit)

**Analog:** `tests/test_calibration.py`

**Test pattern:** Similar to `TestCalibrationService` — test static methods with known inputs/outputs. Verify math computations for cone vertices.

---

### `tests/test_layout_dialog.py` (test, unit)

**Analog:** `tests/test_calibration.py`

**Test pattern:** Similar to `TestCalibrationViewModel` — test ViewModel state transitions. Use `qapp` fixture for Qt widget tests.

---

## Shared Patterns

### Domain Service Pattern
**Source:** `src/house_photo_mapper/domain/services/calibration.py`
**Apply to:** All domain service files
```python
class CalibrationService:
    """Stateless service for computing and verifying plan scale calibration.
    
    All methods are static — no state is held between calls. Calibration
    operates entirely in scene coordinates (world units), making the result
    invariant to viewport zoom/pan/rotate.
    """
    
    @staticmethod
    def calibrate(
        point1: QPointF,
        point2: QPointF,
        known_distance_m: float,
    ) -> CalibrationModel:
        """Compute pixels-per-meter from two scene points and a known real-world distance.
        
        Args:
            point1: First reference point in scene coordinates.
            point2: Second reference point in scene coordinates.
            known_distance_m: Known real-world distance between the points in meters.
        
        Returns:
            CalibrationModel with computed ppm, marked as not yet verified.
        
        Raises:
            ValueError: If known_distance_m <= 0 or pixel distance <= 0.
        """
        if known_distance_m <= 0:
            raise ValueError("known_distance_m must be > 0")
        
        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        pixel_dist = math.hypot(dx, dy)
        
        if pixel_dist <= 0:
            raise ValueError("pixel distance must be > 0 (points are identical)")
        
        ppm = pixel_dist / known_distance_m
        
        return CalibrationModel(
            pixels_per_meter=ppm,
            verified=False,
            reference_point1=[point1.x(), point1.y()],
            reference_point2=[point2.x(), point2.y()],
            reference_distance_m=known_distance_m,
        )
```

### Background Processing Pattern
**Source:** `src/house_photo_mapper/domain/services/tile_pyramid.py`
**Apply to:** `report_generator.py`
```python
def render_tile_worker(pdf_path: str, spec: TileSpec) -> bytes:
    """Worker function to render a single tile in a separate process.
    
    Opens its own document handle (PyMuPDF is not thread-safe).
    Returns PNG bytes for efficient caching.
    
    Args:
        pdf_path: Path to PDF file.
        spec: Tile specification.
    
    Returns:
        PNG bytes of the rendered tile.
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[spec.page_num]
        zoom = spec.dpi / 72.0
        tile_pts = TILE_SIZE / zoom
        clip = fitz.Rect(
            spec.tile_x * tile_pts,
            spec.tile_y * tile_pts,
            (spec.tile_x + 1) * tile_pts,
            (spec.tile_y + 1) * tile_pts,
        )
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False, colorspace=fitz.csRGB)
        return pix.tobytes("png")
    finally:
        doc.close()
        fitz.TOOLS.store_shrink(100)
```

### ViewModel Pattern
**Source:** `src/house_photo_mapper/presentation/viewmodels/calibration_vm.py`
**Apply to:** All ViewModel files
```python
class CalibrationViewModel(QtSafeViewModel):
    """ViewModel for the calibration dialog wizard.
    
    Manages 5-step wizard state. Emits signals for UI updates.
    Connects to PlanGraphicsView event filter for point capture.
    """
    
    # Signals
    step_changed = Signal(int)              # Emits new CalibrationStep value
    calibration_ready = Signal(object)      # Emits CalibrationModel on accept
    cancelled = Signal()                    # Emits when user cancels
    error_message = Signal(str)             # Emits validation error messages
    
    def __init__(self, parent=None) -> None:
        """Initialize CalibrationViewModel.
        
        Args:
            parent: Parent QObject for memory management.
        """
        super().__init__(parent)
        self._step = CalibrationStep.SPEC
        self._known_distance_m: float = 0.0
        self._calibration = None  # CalibrationModel or None
        self._error_pct: float | None = None
```

### Dialog Pattern
**Source:** `src/house_photo_mapper/presentation/views/calibration_dialog.py`
**Apply to:** All dialog files
```python
class CalibrationDialog(QDialog):
    """Dialog guiding user through 5-step calibration wizard.
    
    Uses QStackedWidget for step-by-step navigation. Installs event
    filter on PlanGraphicsView to capture clicks in scene coordinates.
    """
    
    def __init__(
        self,
        vm: CalibrationViewModel,
        plan_view: "PlanGraphicsView | None" = None,
        parent=None,
    ) -> None:
        """Initialize CalibrationDialog.
        
        Args:
            vm: CalibrationViewModel to bind to.
            plan_view: PlanGraphicsView for click capture (optional for testing).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._vm = vm
        self._plan_view = plan_view
        
        self.setWindowTitle("Calibrate Plan Scale")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Install event filter on plan view for click capture
        if self._plan_view is not None:
            self._plan_view.viewport().installEventFilter(self)
        
        self._setup_ui()
        self._connect_signals()
        
        # Initialize UI state
        self._on_step_changed(int(self._vm.step))
```

### Error Handling Pattern
**Source:** `src/house_photo_mapper/domain/services/calibration.py`
**Apply to:** All service files
```python
if known_distance_m <= 0:
    raise ValueError("known_distance_m must be > 0")

if pixel_dist <= 0:
    raise ValueError("pixel distance must be > 0 (points are identical)")
```

### Test Fixture Pattern
**Source:** `tests/conftest.py`
**Apply to:** All test files
```python
@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for the entire test session.
    
    This fixture creates a single QApplication instance that is reused
    across all tests, which is required by Qt.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("HousePhotoMapper-Test")
        app.setOrganizationName("HousePhotoMapper-Test")
    yield app
    # QApplication cleanup is handled by Qt
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/house_photo_mapper/domain/services/report_generator.py` | service | file-I/O | No ReportLab integration exists yet; use RESEARCH.md Pattern 1 |
| `src/house_photo_mapper/domain/services/camera_overlay.py` | service | transform | No drawing overlay service exists yet; use RESEARCH.md Pattern 3 |

## Metadata

**Analog search scope:** `src/house_photo_mapper/domain/services/`, `src/house_photo_mapper/presentation/viewmodels/`, `src/house_photo_mapper/presentation/views/`, `tests/`
**Files scanned:** 15
**Pattern extraction date:** 2026-07-15
