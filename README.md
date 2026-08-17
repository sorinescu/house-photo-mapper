# HousePhotoMapper

A desktop application for correlating building photographs with 2D architectural floor plans and generating professional PDF documentation reports.

## Features

- **Plan import** — Import PDF architectural plans (multi-page supported). Plans display in a zoomable/pannable viewport with per-page calibration.
- **Photo import** — Bulk-import hundreds of photos at once. EXIF metadata (camera, lens, timestamp) is extracted automatically.
- **Annotation** — Place each photo on the correct plan page by clicking to set camera position, then drag to set viewing direction and cone angle. Visible area rectangles are supported.
- **Report generation** — Export a professional PDF report with one page per annotation: header with plan page name and annotation title, the photograph, and the full plan page with camera overlay (marker, direction arrow, viewing cone).
- **Report configuration** — Choose page format (A4 / US Letter), orientation (Portrait / Landscape), and annotation color mode (original colors or a custom override color). All settings persist across sessions.
- **Project persistence** — Save and reopen projects. Auto-save with configurable interval. Crash recovery from `.bak` files.
- **Multi-page navigation** — Sidebar with thumbnails, move-to-reorder, and rename. Per-page floor assignment.
- **Undo/redo** — Full undo stack for annotation creation, deletion, and property changes.
- **Dark/light theme** — Automatic system theme detection with manual toggle.

## Requirements

- Python 3.12+
- macOS (primary), Windows/Linux (not yet packaged)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd house-photo-mapper

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## Running

```bash
python -m house_photo_mapper
```

## Running Tests

```bash
pytest
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | PySide6 (Qt 6) |
| PDF rendering | PyMuPDF |
| PDF generation | ReportLab |
| Image processing | Pillow, pillow-heif |
| Data models | Pydantic v2 |
| Logging | structlog |
| Build | Hatchling |
| Packaging | pyappdist |

## Project Structure

```
src/house_photo_mapper/
├── domain/
│   ├── models/          # Data models (Project, Plan, Annotation, Photo)
│   └── services/        # Business logic (report generation, plan rendering, persistence)
├── infrastructure/      # Autosave, logging, theme, Qt patterns
├── presentation/
│   ├── views/           # Qt widgets (MainWindow, PlanView, sidebar, dialogs)
│   ├── viewmodels/      # MVVM viewmodels
│   └── graphics/        # QGraphicsItem subclasses for annotations
└── fonts/               # NotoSans font files for Unicode support
```

## License

MIT.
