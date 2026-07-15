# Phase 6: Report Generation - Research

**Researched:** 2026-07-15
**Domain:** PDF report generation with programmatic layout, image compositing, and background processing
**Confidence:** HIGH

## Summary

Phase 6 generates professional PDF reports from the HousePhotoMapper project data. Each page contains a photo, an annotated plan snippet centered on the camera position with camera symbol and viewing cone overlay, annotation title/description, EXIF metadata, and auto-incrementing figure numbers. The user selects A4 Portrait, A4 Landscape, or US Letter layout before generation. Reports generate in the background without freezing the UI, with a 50-photo report completing in under 30 seconds.

**Primary recommendation:** Use ReportLab's low-level canvas API (not Platypus flowables) for the per-page composition since each page has a fixed, precise layout. Use `BaseDocTemplate` with `PageTemplate` only for page size/margin switching. Render plan snippets via PyMuPDF's `page.get_pixmap(clip=...)` at report DPI. Run generation in a `ProcessPoolExecutor` (already used in TilePyramid) with `QThread`-based progress reporting.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RG-01 | User can generate professional PDF report | ReportLab canvas API: `canvas.Canvas(filename, pagesize=...)` — precise coordinate control for fixed layouts [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/] |
| RG-02 | Report includes photo on each page | `canvas.drawImage(image, x, y, width, height)` with PIL ImageReader for photo placement [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/] |
| RG-03 | Report includes annotated plan snippet | PyMuPDF `page.get_pixmap(matrix=mat, clip=rect)` renders plan region at report DPI [CITED: pymupdf.readthedocs.io/en/latest/recipes-images.html] |
| RG-04 | Report includes camera symbol and viewing cone | Canvas drawing primitives: `canvas.circle()`, `canvas.lines()`, `canvas.setFillColor()`, `canvas.setStrokeColor()` — draw directly on PDF [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/] |
| RG-05 | Report includes annotation title and description | `canvas.drawString()` and `canvas.setFont()` for text placement [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/] |
| RG-06 | Report includes photo metadata (timestamp, camera, lens) | `canvas.drawString()` with EXIF data from `PhotoModel.exif` (ExifModel) [ASSUMED] |
| RG-07 | Report includes figure numbers | Auto-incrementing counter in page loop, drawn via `canvas.drawString()` [ASSUMED] |
| RG-08 | User can select A4 Portrait/Landscape or Letter layout | ReportLab `A4`, `landscape(A4)`, `letter` from `reportlab.lib.pagesizes` [CITED: docs.reportlab.com/reportlab/userguide/ch5_platypus/] |
</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

*No CONTEXT.md exists for this phase. No locked decisions, discretion areas, or deferred ideas to constrain research.*
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PDF page composition | Domain Service | — | Report generation is pure data→PDF, no UI dependency |
| Plan snippet rendering | Domain Service | Infrastructure | PyMuPDF rendering lives in domain (like PlanRenderer) |
| Camera symbol + cone overlay | Domain Service | — | Drawing logic is math/geometry, not UI |
| Background generation | Infrastructure | Domain | ProcessPoolExecutor + QThread progress is infra pattern |
| Export settings UI | Presentation | — | Layout selection dialog is Qt widget |
| ReportViewModel | Presentation | Domain | Bridges UI actions to report generation service |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reportlab | 4.4+ | PDF generation — canvas API for precise coordinate control | Industry standard for programmatic PDF in Python; already decided in STATE.md decisions |
| pymupdf | 1.26+ | Plan snippet rendering via `get_pixmap(clip=...)` | Already a project dependency; excellent clip rendering with DPI control |
| pillow | 12.3+ | Photo loading, EXIF orientation, image format conversion | Already a project dependency; required by ReportLab for ImageReader |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| reportlab.lib.pagesizes | — | A4, letter, landscape constants | Page size selection (RG-08) |
| reportlab.graphics.shapes | — | Drawing primitives for camera symbol/cone | Overlay rendering on PDF canvas |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ReportLab canvas | Platypus flowables | Canvas gives precise coordinate control needed for fixed-layout photo+plan pages; Platypus is better for flowing text documents |
| ProcessPoolExecutor | QThreadPool | ProcessPool already proven in TilePyramid; avoids GIL for CPU-bound PDF generation |
| PyMuPDF for plan snippets | Pillow + fitz | PyMuPDF's `get_pixmap(clip=...)` handles DPI scaling and rotation natively; no need for extra Pillow step |

**Installation:**
```bash
pip install reportlab>=4.4
```

**Version verification:** Before writing the Standard Stack table, verify each recommended package exists and is current using the ecosystem-appropriate command:
```bash
pip show reportlab  # verify installed version
pip index versions reportlab  # check latest available
```

## Package Legitimacy Audit

> **Required** whenever this phase installs external packages. Run the Package Legitimacy Gate protocol before completing this section.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| reportlab | PyPI | 24+ years | 50M+/month | [github.com/reportlab/reportlab](https://github.com/reportlab/reportlab) | OK | Approved |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
User clicks "Generate Report"
        │
        ▼
ReportViewModel.generate_report()
        │
        ├─► Show LayoutDialog (A4 Portrait/Landscape, Letter)
        │       │
        │       ▼
        │   ExportSettings updated
        │
        ├─► ReportGeneratorService.generate()
        │       │
        │       ├─► For each annotation:
        │       │       ├─► Load photo (PIL)
        │       │       ├─► Render plan snippet (PyMuPDF get_pixmap with clip)
        │       │       ├─► Draw camera symbol + cone (math→canvas coords)
        │       │       └─► Compose page (ReportLab canvas)
        │       │
        │       └─► Save PDF
        │
        └─► Progress dialog (QThread signal → UI update)
```

### Recommended Project Structure
```
src/house_photo_mapper/
├── domain/services/
│   ├── report_generator.py      # Core PDF generation logic
│   ├── plan_snippet.py          # PyMuPDF plan region rendering
│   └── camera_overlay.py        # Camera symbol + cone drawing math
├── presentation/
│   ├── viewmodels/
│   │   └── report_vm.py         # ReportViewModel (generate, progress, cancel)
│   └── views/
│       ├── layout_dialog.py     # A4/Letter/Portrait/Landscape selection
│       └── report_progress.py   # Progress dialog during generation
```

### Pattern 1: Canvas-Based Fixed-Page Composition
**What:** Use ReportLab's low-level `canvas.Canvas` API for precise coordinate placement on each page, not Platypus flowables.
**When to use:** When every page has the exact same fixed layout (photo at position X, plan snippet at position Y, text at position Z). Platypus is for flowing content; this phase has rigid layouts.
**Example:**
```python
# Source: [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/]
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

c = canvas.Canvas("report.pdf", pagesize=A4)
width, height = A4  # 595.27 x 841.89 points

# Photo — top half of page
c.drawImage("photo.jpg", 50, height - 350, width=width - 100, height=300)

# Plan snippet — bottom half
c.drawImage("plan_snippet.png", 50, 50, width=width - 100, height=250)

# Title text
c.setFont("Helvetica-Bold", 14)
c.drawString(50, height - 370, "Figure 1: Living Room")

# Metadata
c.setFont("Helvetica", 9)
c.drawString(50, 30, "Canon EOS R5 | 24-70mm | 2024-01-15 14:30")

c.showPage()
c.save()
```

### Pattern 2: Plan Snippet Extraction with PyMuPDF
**What:** Render a region of a plan page centered on the camera position at report DPI.
**When to use:** For each annotation, extract the plan area around the camera marker.
**Example:**
```python
# Source: [CITED: pymupdf.readthedocs.io/en/latest/recipes-images.html]
import fitz  # PyMuPDF

def render_plan_snippet(
    pdf_path: str,
    page_index: int,
    center_x: float,  # scene coordinates
    center_y: float,
    zoom_radius: float,  # how much of the plan to show (meters)
    pixels_per_meter: float,
    target_width_px: int,
    target_height_px: int,
) -> bytes:
    """Render plan region centered on camera at report DPI."""
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    # Convert scene coords to page coords (PDF points)
    # Scene coords are in pixels at pixels_per_meter scale
    # PDF page coords are in points (72 DPI)
    page_center_x = center_x / pixels_per_meter * 72
    page_center_y = center_y / pixels_per_meter * 72
    radius_pts = zoom_radius * 72

    clip = fitz.Rect(
        page_center_x - radius_pts,
        page_center_y - radius_pts,
        page_center_x + radius_pts,
        page_center_y + radius_pts,
    )

    # Ensure clip stays within page bounds
    clip = clip & page.rect

    # Calculate zoom to fit target dimensions
    zoom_x = target_width_px / clip.width
    zoom_y = target_height_px / clip.height
    zoom = min(zoom_x, zoom_y)

    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    png_bytes = pix.tobytes("png")

    doc.close()
    return png_bytes
```

### Pattern 3: Camera Symbol + Viewing Cone Drawing
**What:** Draw camera marker (circle), direction arrow, and viewing cone polygon on the plan snippet.
**When to use:** Overlay on each plan snippet in the PDF.
**Example:**
```python
# Drawing camera symbol on ReportLab canvas
import math

def draw_camera_overlay(
    c: canvas.Canvas,
    center_x: float, center_y: float,  # in PDF points on the snippet
    direction_angle: float,  # degrees, 0=right, CCW
    cone_angle: float,  # degrees
    color: str = "#DC2828",
    marker_radius: float = 6,
    cone_length: float = 40,
):
    """Draw camera symbol and viewing cone on canvas."""
    from reportlab.lib.colors import HexColor

    c.saveState()
    c.setFillColor(HexColor(color))
    c.setStrokeColor(HexColor(color))

    # Camera marker (circle)
    c.circle(center_x, center_y, marker_radius, fill=1)

    # Direction arrow
    rad = math.radians(direction_angle)
    dx = 20 * math.cos(rad)
    dy = 20 * math.sin(rad)
    c.setLineWidth(2)
    c.line(center_x, center_y, center_x + dx, center_y + dy)

    # Viewing cone (triangle)
    half_cone = math.radians(cone_angle / 2)
    left_rad = rad + half_cone
    right_rad = rad - half_cone

    tip = (center_x, center_y)
    left = (
        center_x + cone_length * math.cos(left_rad),
        center_y + cone_length * math.sin(left_rad),
    )
    right = (
        center_x + cone_length * math.cos(right_rad),
        center_y + cone_length * math.sin(right_rad),
    )

    c.setFillColor(HexColor(color + "1A"))  # ~10% opacity
    c.setStrokeColor(HexColor(color + "99"))  # ~60% opacity
    c.setLineWidth(1)
    c.setDash(3, 2)  # dashed line
    c.setFillColor(HexColor(color + "1A"))
    c.beginPath()
    c.moveTo(*tip)
    c.lineTo(*left)
    c.lineTo(*right)
    c.close()
    c.drawPath(fill=1, stroke=1)

    c.restoreState()
```

### Pattern 4: Background Generation with Progress
**What:** Run PDF generation in a separate process, report progress to UI via Qt signals.
**When to use:** Always — report generation must not freeze UI (success criterion 6).
**Example:**
```python
# Source: [ASSUMED — pattern from existing TilePyramid]
from concurrent.futures import ProcessPoolExecutor
from PySide6.QtCore import QThread, Signal

def generate_page_worker(args: tuple) -> bytes:
    """Worker function for single page generation in subprocess."""
    # args contains all data needed for one page
    # Returns PDF page as bytes (or writes to temp file)
    ...

class ReportGenerationWorker(QThread):
    """Background worker for report generation with progress."""
    progress = Signal(int, int)  # (current, total)
    finished = Signal(str)  # output path
    error = Signal(str)

    def __init__(self, pages_data, output_path, settings):
        super().__init__()
        self._pages_data = pages_data
        self._output_path = output_path
        self._settings = settings
        self._cancelled = False

    def run(self):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4, letter

            page_size = self._get_page_size()
            c = canvas.Canvas(self._output_path, pagesize=page_size)

            for i, page_data in enumerate(self._pages_data):
                if self._cancelled:
                    break
                self._render_page(c, page_data, i + 1, page_size)
                c.showPage()
                self.progress.emit(i + 1, len(self._pages_data))

            c.save()
            if not self._cancelled:
                self.finished.emit(self._output_path)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True
```

### Anti-Patterns to Avoid
- **Platypus flowables for fixed layouts:** Each page has identical structure (photo + plan + text). Platypus adds unnecessary complexity for paginating flowing content when you need exact coordinate control.
- **Building entire PDF in memory:** ReportLab's `canvas.Canvas` streams to disk incrementally. Don't buffer the whole PDF in memory for 50+ pages.
- **Per-cell Paragraph objects in tables:** Avoid wrapping metadata in ReportLab `Paragraph` flowables — use plain strings with `canvas.drawString()` for small fixed text blocks.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation | Custom PDF writer | ReportLab canvas | PDF spec is complex; ReportLab handles fonts, images, compression, metadata |
| Plan snippet rendering | Custom rasterizer | PyMuPDF `get_pixmap(clip=...)` | PyMuPDF handles DPI scaling, rotation, color spaces natively |
| Image format conversion | Custom PIL→PDF pipeline | ReportLab `ImageReader` | Handles JPEG/PNG/TIFF transparently with memory efficiency |
| EXIF metadata display | Custom metadata parser | `PhotoModel.exif` (ExifModel) | Already extracted in Phase 3; just format for display |

**Key insight:** ReportLab handles all the PDF internals (fonts, compression, cross-references, metadata). Never write raw PDF bytes.

## Common Pitfalls

### Pitfall 1: ReportLab O(n²) Table Layout
**What goes wrong:** Using `Table` flowable with many rows causes exponential slowdown as ReportLab pre-computes the entire layout.
**Why it happens:** `Table` computes column widths and row heights for all rows before rendering. With 50+ photos, this creates massive overhead.
**How to avoid:** Don't use `Table` for report layout. Use `canvas.drawString()` for text and `canvas.drawImage()` for images — these are O(1) per element. If tables are needed for metadata, use `LongTable` (streaming layout) or keep tables small (one photo's metadata per page, not all photos in one table).
**Warning signs:** Generation time exceeding 30 seconds for 50 photos.

### Pitfall 2: PyMuPDF Clip Rectangle Rotation
**What goes wrong:** `get_pixmap(clip=...)` returns wrong region when the PDF page is rotated.
**Why it happens:** PyMuPDF coordinates are relative to the unrotated page. Clip rectangles must account for page rotation.
**How to avoid:** Check `page.rotation` and adjust clip coordinates accordingly. Use `page.rect` (which reflects rotation) vs raw coordinates.
**Warning signs:** Plan snippets showing wrong area or garbled content.

### Pitfall 3: ProcessPoolExecutor Pickling
**What goes wrong:** Passing complex objects (Pydantic models, Qt objects) to subprocess workers fails with pickle errors.
**Why it happens:** `ProcessPoolExecutor` uses pickle to send data to worker processes. Qt objects and some Pydantic models aren't picklable.
**How to avoid:** Pass only primitive data (strings, numbers, lists, dicts) to workers. Serialize all inputs to simple types before submitting tasks.
**Warning signs:** `PicklingError` or `TypeError` when submitting tasks.

### Pitfall 4: Memory Explosion with Large Photos
**What goes wrong:** Loading 50 high-res photos (4000×3000) simultaneously exhausts memory.
**Why it happens:** Each uncompressed photo is ~48MB in memory. 50 photos = ~2.4GB.
**How to avoid:** Process photos sequentially in the worker, not all at once. Use PIL's lazy loading and resize to report dimensions immediately.
**Warning signs:** `MemoryError` or system slowdown during generation.

### Pitfall 5: Canvas Coordinate System Confusion
**What goes wrong:** Elements placed at wrong positions because ReportLab's origin is bottom-left (not top-left like screen coordinates).
**Why it happens:** ReportLab uses PDF coordinate system: (0,0) is bottom-left, Y increases upward. Most developers think in top-left origin.
**How to avoid:** Always use `height - y` to convert from top-down thinking. Draw from top of page downward: start at `height - margin`, subtract element heights.
**Warning signs:** Text/images appearing at bottom of page or overlapping.

## Code Examples

Verified patterns from official sources:

### Basic ReportLab Canvas with Image and Text
```python
# Source: [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/]
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib.utils import ImageReader

def create_report_page(c, photo_path, plan_snippet_bytes, title, metadata, figure_num, page_size):
    """Render one photo's report page."""
    width, height = page_size
    margin = 20 * 2.835  # 20mm in points (1mm = 2.835 points)

    # --- Photo (top 55% of usable area) ---
    photo_height = (height - 2 * margin) * 0.55
    photo_width = width - 2 * margin
    photo_y = height - margin - photo_height

    img = ImageReader(photo_path)
    c.drawImage(img, margin, photo_y, width=photo_width, height=photo_height,
                preserveAspectRatio=True, anchor='nw')

    # --- Figure number + title ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, photo_y - 20, f"Figure {figure_num}: {title}")

    # --- Plan snippet ---
    plan_y = photo_y - 40 - plan_height
    snippet_img = ImageReader(plan_snippet_bytes)
    c.drawImage(snippet_img, margin, plan_y, width=plan_width, height=plan_height)

    # --- Metadata ---
    c.setFont("Helvetica", 8)
    meta_text = f"{metadata['camera']} | {metadata['lens']} | {metadata['date']}"
    c.drawString(margin, plan_y - 15, meta_text)
```

### Page Size Selection
```python
# Source: [CITED: docs.reportlab.com/reportlab/userguide/ch5_platypus/]
from reportlab.lib.pagesizes import A4, letter, landscape

PAGE_SIZES = {
    "A4 Portrait": A4,                    # (595.27, 841.89)
    "A4 Landscape": landscape(A4),        # (841.89, 595.27)
    "US Letter": letter,                  # (612.00, 792.00)
}
```

### Plan Snippet with PyMuPDF Clip
```python
# Source: [CITED: pymupdf.readthedocs.io/en/latest/recipes-images.html]
import fitz

def extract_plan_snippet(pdf_path, page_index, camera_x, camera_y,
                         pixels_per_meter, radius_meters=5.0, dpi=150):
    """Extract plan region centered on camera position."""
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    # Convert scene coordinates to PDF points
    # Scene coords are pixels at pixels_per_meter scale
    pdf_center_x = (camera_x / pixels_per_meter) * 72  # 72 DPI = 1.0 scale
    pdf_center_y = (camera_y / pixels_per_meter) * 72
    radius_pts = radius_meters * 72

    clip = fitz.Rect(
        pdf_center_x - radius_pts,
        pdf_center_y - radius_pts,
        pdf_center_x + radius_pts,
        pdf_center_y + radius_pts,
    ) & page.rect  # Clamp to page bounds

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)

    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Platypus flowables for all PDFs | Canvas API for fixed layouts | ReportLab 3.x+ | Better performance and control for structured reports |
| PyMuPDF IRect for clips | PyMuPDF Rect for clips | PyMuPDF 1.23.9 | IRect no longer accepted as clip parameter |
| Thread-based background | ProcessPoolExecutor | Python 3.2+ | True parallelism, avoids GIL for CPU-bound PDF generation |

**Deprecated/outdated:**
- `IRect` as clip parameter in `get_pixmap()`: Deprecated in PyMuPDF 1.23.9, use `Rect` instead [CITED: github.com/pymupdf/PyMuPDF/issues/3134]
- `canvas.setFillColorRGB()` with alpha: Use `canvas.setFillColor(HexColor())` with RGBA hex for cleaner color management [ASSUMED]

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this
> section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | EXIF metadata display uses `PhotoModel.exif` fields directly | Code Examples | Low — ExifModel fields are well-defined in Phase 3 |
| A2 | Figure numbers are auto-incrementing integers starting at 1 | Common Pitfalls | Low — standard convention; could be configurable via ExportSettings |
| A3 | Canvas coordinate system uses bottom-left origin (standard PDF) | Common Pitfalls | None — this is PDF specification |
| A4 | Camera symbol uses hex color from annotation's `color` field | Code Examples | Low — annotation model already has `color: str = "#DC2828"` |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **Plan snippet zoom radius**
   - What we know: Camera position and viewing cone are defined in scene coordinates
   - What's unclear: How much of the plan to show around each camera (zoom_radius in meters)
   - Recommendation: Use 5m default radius, make configurable via ExportSettings

2. **Photo aspect ratio handling**
   - What we know: Photos can be any aspect ratio (landscape, portrait, square)
   - What's unclear: Should photos be cropped to fit or letterboxed?
   - Recommendation: Use `preserveAspectRatio=True` with `anchor='nw'` — no cropping, centered in allocated space

3. **Report title page**
   - What we know: ExportSettings has `report_title`, `report_subtitle`, `report_author`
   - What's unclear: Should there be a dedicated title page before the photo pages?
   - Recommendation: Include optional title page if `report_title` is non-empty

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| reportlab | PDF generation | ✗ (not yet installed) | — | Must install before Phase 6 execution |
| pymupdf | Plan snippet rendering | ✓ | 1.26+ | Already in pyproject.toml |
| pillow | Photo loading | ✓ | 12.3+ | Already in pyproject.toml |

**Missing dependencies with no fallback:**
- `reportlab` must be added to `pyproject.toml` dependencies before Phase 6 plans execute

**Missing dependencies with fallback:**
- None — reportlab is the only new dependency and is required

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1+ with pytest-qt 4.5+ |
| Config file | pyproject.toml [tool.pyappdist] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RG-01 | Generate PDF report | integration | `pytest tests/test_report_generator.py -x` | ❌ Wave 0 |
| RG-02 | Photo on each page | unit | `pytest tests/test_report_generator.py::test_photo_placement -x` | ❌ Wave 0 |
| RG-03 | Plan snippet on each page | unit | `pytest tests/test_plan_snippet.py -x` | ❌ Wave 0 |
| RG-04 | Camera symbol + cone | unit | `pytest tests/test_camera_overlay.py -x` | ❌ Wave 0 |
| RG-05 | Title and description | unit | `pytest tests/test_report_generator.py::test_text_placement -x` | ❌ Wave 0 |
| RG-06 | EXIF metadata | unit | `pytest tests/test_report_generator.py::test_metadata_display -x` | ❌ Wave 0 |
| RG-07 | Figure numbers | unit | `pytest tests/test_report_generator.py::test_figure_numbering -x` | ❌ Wave 0 |
| RG-08 | Layout selection | unit | `pytest tests/test_layout_dialog.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ --tb=short`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_report_generator.py` — covers RG-01, RG-02, RG-05, RG-06, RG-07
- [ ] `tests/test_plan_snippet.py` — covers RG-03
- [ ] `tests/test_camera_overlay.py` — covers RG-04
- [ ] `tests/test_layout_dialog.py` — covers RG-08
- [ ] Framework install: `pip install reportlab` — required before any tests

## Security Domain

> Required when `security_enforcement` is enabled (absent = enabled). Omit only if explicitly `false` in config.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Validate photo paths, annotation data before PDF generation |
| V6 Cryptography | no | No crypto operations in report generation |

### Known Threat Patterns for ReportLab Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in photo paths | Tampering | Validate paths are within project directory before loading |
| Memory exhaustion from large images | Denial of Service | Resize images to report dimensions immediately on load |
| Arbitrary file read via plan snippet | Information Disclosure | Validate PDF paths are project plans, not arbitrary files |

## Sources

### Primary (HIGH confidence)
- [CITED: docs.reportlab.com/reportlab/userguide/ch2_graphics/] - Canvas API: drawImage, drawString, drawing primitives
- [CITED: docs.reportlab.com/reportlab/userguide/ch5_platypus/] - Platypus: PageTemplate, Frame, BaseDocTemplate
- [CITED: pymupdf.readthedocs.io/en/latest/recipes-images.html] - PyMuPDF clip rendering, pixmap extraction
- [CITED: pymupdf.readthedocs.io/en/latest/page.html] - Page.get_pixmap() API reference

### Secondary (MEDIUM confidence)
- [CITED: woteq.com/implementing-custom-page-templates-and-frames-in-reportlab-for-python/] - Custom PageTemplate patterns with Frame geometry
- [CITED: nicd.org.uk/knowledge-hub/creating-pdf-reports-with-reportlab-and-pandas] - ReportLab + image conversion patterns

### Tertiary (LOW confidence)
- [ASSUMED] Canvas coordinate system explanation — based on training knowledge of PDF spec
- [ASSUMED] Memory management patterns for large photo batches — based on general Python knowledge

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — ReportLab and PyMuPDF are well-documented, industry-standard libraries with extensive official documentation
- Architecture: HIGH — Pattern follows existing TilePyramid background processing and PlanRenderer service patterns
- Pitfalls: HIGH — O(n²) table issue already identified in STATE.md; clip rotation issue documented in PyMuPDF issues

**Research date:** 2026-07-15
**Valid until:** 2026-08-15 (stable — ReportLab and PyMuPDF APIs are mature)
