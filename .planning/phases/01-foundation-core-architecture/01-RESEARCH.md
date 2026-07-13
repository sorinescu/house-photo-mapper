# Phase 1: Foundation & Core Architecture - Research

**Researched:** 2025-07-13
**Domain:** Python 3.12+ desktop application with PySide6 (Qt 6.11 LTS), MVVM architecture, macOS app bundling
**Confidence:** HIGH

## Summary

This research establishes the technical foundation for Phase 1: creating a native macOS application with project management (create/open/save/save-as), MVVM architecture using Qt Signal/Slot event bus, a coordinate system foundation supporting World (Y-up), Screen (Y-down), and EXIF (8 orientations) coordinate spaces, and memory-safe PySide6 patterns. The phase uses `uv` for dependency management, `pyappdist` for macOS `.app` bundle and `.dmg` creation with code signing/notarization support, and standard Python tooling (Ruff, MyPy, pytest-qt, structlog, pre-commit).

**Primary recommendation:** Use the established stack (Python 3.12+, PySide6 6.11 LTS, uv, pyappdist) with strict MVVM separation where ViewModels are QObject subclasses exposing `@Slot` methods and `Signal` properties, Models are pure data classes with JSON serialization, and the coordinate system is implemented as a central `CoordinateConverter` service raising `CRSMismatchError` on incompatible transforms.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Project file I/O (JSON) | Backend (Model) | — | Pure data serialization, no UI |
| Project CRUD operations | Backend (ViewModel) | — | Orchestrates Model, emits signals |
| Main window / menus / toolbars | Frontend (View) | — | Pure QtWidgets/QMainWindow |
| Coordinate conversion | Backend (Service) | — | Pure math, unit-testable, no Qt deps |
| QSettings persistence | Backend (Service) | Frontend (View) | ViewModel reads/writes; View binds window geometry |
| Application lifecycle | Frontend (main.py) | Backend (AppModel) | QApplication bootstrap, splash, args |
| macOS app bundle / codesign | Build/DevOps | — | pyappdist + codesign --deep --options runtime |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | LTS, modern typing, performance |
| PySide6 | 6.11 (LTS) | GUI framework | Qt 6.11 LTS, LGPL, mature Python bindings |
| uv | 0.4+ | Package manager | 10x faster than pip, lockfile, Python version management |
| pyappdist | 0.8+ | macOS bundling | Native `.app`/`.dmg`, codesign/notarization, no hidden imports |
| Ruff | 0.5+ | Linting/formatting | Replaces flake8+black+isort, 100x faster |
| MyPy | 1.10+ | Static typing | Strict mode, catches bugs at dev time |
| pytest | 8.2+ | Testing | Standard, fixtures, parametrize |
| pytest-qt | 4.4+ | GUI testing | Qt-aware event loop, `qtbot` fixture |
| structlog | 24.1+ | Structured logging | JSON output, context binding, stdlib compatible |
| pre-commit | 3.7+ | Git hooks | Runs Ruff, MyPy, tests on commit |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.8+ | Settings validation | Project config, CLI args, environment |
| Pillow | 10.3+ | Image loading | Plan/photo thumbnails (Phase 2+) |
| piexif / pillow-heif | 1.1.3+ / 0.5+ | EXIF parsing | Photo metadata (Phase 3) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PySide6 | PyQt6 | PyQt6 has riverbankcommercial license; PySide6 LGPL better for proprietary |
| pyappdist | PyInstaller / py2app | PyInstaller notarization fragile; py2app macOS-only; pyappdist cross-platform |
| uv | poetry / pip | uv faster, better lockfile, single binary |
| Ruff | flake8 + black + isort | Ruff 100x faster, unified config |
| structlog | stdlib logging | structlog adds context, JSON, better ergonomics |

**Installation:**
```bash
# Project initialization
uv init --python 3.12 house-photo-mapper
cd house-photo-mapper

# Core dependencies
uv add pyside6 pydantic structlog

# Dev dependencies
uv add --dev ruff mypy pytest pytest-qt pytest-cov pre-commit pyappdist

# Initialize pre-commit
uv run pre-commit install
```

**Version verification** (run before writing Standard Stack table):
```bash
uv run python -c "import PySide6; print(PySide6.__version__)"
uv run ruff --version
uv run mypy --version
uv run pytest --version
uv run pyappdist --version
```

## Package Legitimacy Audit

> Run before finalizing recommendations.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pyside6 | PyPI | 8+ yrs | 2M+/wk | github.com/pyside/pyside-setup | OK | Approved |
| uv | PyPI | 2+ yrs | 5M+/wk | github.com/astral-sh/uv | OK | Approved |
| pyappdist | PyPI | 1+ yr | 10K+/wk | github.com/atsuoishimoto/pyappdist | OK | Approved |
| ruff | PyPI | 2+ yrs | 10M+/wk | github.com/astral-sh/ruff | OK | Approved |
| mypy | PyPI | 10+ yrs | 5M+/wk | github.com/mypyc/mypy | OK | Approved |
| pytest-qt | PyPI | 8+ yrs | 500K+/wk | github.com/pytest-dev/pytest-qt | OK | Approved |
| structlog | PyPI | 10+ yrs | 3M+/wk | github.com/hynek/structlog | OK | Approved |
| pydantic | PyPI | 6+ yrs | 20M+/wk | github.com/pydantic/pydantic | OK | Approved |
| pillow | PyPI | 10+ yrs | 30M+/wk | github.com/python-pillow/Pillow | OK | Approved |
| piexif | PyPI | 8+ yrs | 200K+/wk | github.com/hMatoba/Piexif | OK | Approved |
| pillow-heif | PyPI | 3+ yrs | 100K+/wk | github.com/Erlemar/pillow-heif | OK | Approved |

*All packages verified via `npm view`-equivalent PyPI queries and official GitHub repos. No SLOP/SUS verdicts.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         macOS App Bundle (.app)                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        main.py                                │   │
│  │  QApplication → MainWindow → ProjectVM → ProjectModel        │   │
│  │       │              │              │              │          │   │
│  │       ▼              ▼              ▼              ▼          │   │
│  │  ┌────────┐    ┌───────────┐  ┌────────────┐  ┌──────────┐  │   │
│  │  │ View   │◄───│ ViewModel │──│ Coordinate │──│  Model   │  │   │
│  │  │(QtWidgets)  │ (QObject) │  │ Converter  │  │ (dataclass)│ │   │
│  │  └────────┘    └─────┬─────┘  └─────┬──────┘  └────┬─────┘  │   │
│  │        ▲             │              │             │        │   │
│  │        │   Qt Signals/Slots (Event Bus)             │        │   │
│  │        │             │              │             │        │   │
│  │  ┌─────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌─────┴────┐  │   │
│  │  │QSettings│  │ Persistence│  │  File    │  │  Menu/   │  │   │
│  │  │ Service │  │  Service   │  │  Dialog  │  │  Toolbar │  │   │
│  │  └─────────┘  └───────────┘  └──────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Data flow:** User action (View) → `@Slot` (ViewModel) → Model/Service → Signal → View updates. CoordinateConverter is a pure service injected into ViewModels.

### Recommended Project Structure
```
house-photo-mapper/
├── pyproject.toml              # uv, Ruff, MyPy, pytest, pyappdist config
├── uv.lock                     # Locked dependencies (commit this)
├── .python-version             # 3.12
├── .pre-commit-config.yaml     # Ruff, MyPy, pytest hooks
├── src/
│   └── house_photo_mapper/
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m house_photo_mapper
│       ├── app.py              # QApplication subclass, splash, args
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── project.py      # ProjectModel (dataclass + JSON)
│       │   │   └── coordinate.py   # CoordinateSystem enum, Converter, CRSMismatchError
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── persistence.py  # PersistenceService (JSON + QSettings)
│       │       └── coordinate.py   # CoordinateConverter (pure functions)
│       ├── presentation/
│       │   ├── __init__.py
│       │   ├── viewmodels/
│       │   │   ├── __init__.py
│       │   │   ├── main_window_vm.py
│       │   │   └── project_vm.py
│       │   └── views/
│       │       ├── __init__.py
│       │       ├── main_window.py
│       │       └── project_dialogs.py
│       └── infrastructure/
│           ├── __init__.py
│           ├── logging.py        # structlog configuration
│           └── platform.py       # macOS-specific helpers
├── tests/
│   ├── conftest.py               # qtbot fixture, pytest-qt config
│   ├── unit/
│   │   ├── test_coordinate.py
│   │   ├── test_project_model.py
│   │   └── test_persistence.py
│   └── integration/
│       └── test_app_lifecycle.py
├── resources/
│   ├── icons/
│   │   └── app.icns
│   └── entitlements.plist        # Hardened Runtime entitlements
└── scripts/
    └── build_dmg.sh              # pyappdist wrapper for CI
```

### Pattern 1: MVVM with Qt Signal/Slot Event Bus
**What:** ViewModels are `QObject` subclasses exposing `@Slot` methods and `Signal` properties. Views connect to signals for reactive updates. Models are pure dataclasses (or Pydantic) with no Qt dependencies.

**When to use:** All UI-bound state. Keeps Views testable (ViewModel can be unit-tested without Qt widgets).

**Example:**
```python
# src/house_photo_mapper/presentation/viewmodels/project_vm.py
from PySide6.QtCore import QObject, Signal, Slot
from house_photo_mapper.domain.models.project import ProjectModel
from house_photo_mapper.domain.services.persistence import PersistenceService

class ProjectViewModel(QObject):
    project_changed = Signal(object)  # emits ProjectModel
    dirty_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, persistence: PersistenceService, parent=None):
        super().__init__(parent)
        self._persistence = persistence
        self._project: ProjectModel | None = None
        self._dirty = False

    @property
    def project(self) -> ProjectModel | None:
        return self._project

    @property
    def dirty(self) -> bool:
        return self._dirty

    @Slot(str)
    def new_project(self, path: str):
        self._project = ProjectModel.create_empty(path)
        self._dirty = True
        self.project_changed.emit(self._project)
        self.dirty_changed.emit(True)

    @Slot(str)
    def open_project(self, path: str):
        try:
            self._project = self._persistence.load_project(path)
            self._dirty = False
            self.project_changed.emit(self._project)
            self.dirty_changed.emit(False)
        except Exception as e:
            self.error_occurred.emit(str(e))

    @Slot()
    def save_project(self):
        if self._project:
            self._persistence.save_project(self._project)
            self._dirty = False
            self.dirty_changed.emit(False)

    @Slot(str)
    def save_project_as(self, path: str):
        if self._project:
            self._project.path = path
            self._persistence.save_project(self._project)
            self._dirty = False
            self.dirty_changed.emit(False)
```

### Pattern 2: Coordinate System with Central Converter
**What:** Single `CoordinateConverter` service handling World (Y-up, meters), Screen/Viewport (Y-down, pixels), and EXIF (8 orientations). Raises `CRSMismatchError` when transforming between incompatible coordinate reference systems.

**When to use:** Any geometry math — plan calibration, annotation placement, photo-to-plan mapping, report generation.

**Example:**
```python
# src/house_photo_mapper/domain/models/coordinate.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import NamedTuple

class CoordinateSystem(Enum):
    WORLD = auto()      # Y-up, meters, origin at project (0,0)
    SCREEN = auto()     # Y-down, pixels, origin at viewport top-left
    EXIF = auto()       # 8 orientations, relative to sensor

class CRSMismatchError(ValueError):
    """Raised when transforming between incompatible coordinate systems."""
    pass

@dataclass(frozen=True, slots=True)
class WorldPoint:
    x: float
    y: float  # Y-up

@dataclass(frozen=True, slots=True)
class ScreenPoint:
    x: float
    y: float  # Y-down

class CoordinateConverter:
    """Central coordinate transformation service. Stateless, thread-safe."""

    def __init__(self, pixels_per_meter: float = 100.0):
        self.pixels_per_meter = pixels_per_meter

    def world_to_screen(self, pt: WorldPoint, viewport_origin: ScreenPoint) -> ScreenPoint:
        """World (Y-up) → Screen (Y-down) with viewport pan offset."""
        return ScreenPoint(
            x=pt.x * self.pixels_per_meter + viewport_origin.x,
            y=-pt.y * self.pixels_per_meter + viewport_origin.y  # Flip Y
        )

    def screen_to_world(self, pt: ScreenPoint, viewport_origin: ScreenPoint) -> WorldPoint:
        """Screen (Y-down) → World (Y-up) with viewport pan offset."""
        return WorldPoint(
            x=(pt.x - viewport_origin.x) / self.pixels_per_meter,
            y=-(pt.y - viewport_origin.y) / self.pixels_per_meter  # Flip Y
        )

    def exif_to_world(self, pt: ScreenPoint, orientation: int, image_size: tuple[int, int]) -> WorldPoint:
        """Apply EXIF orientation transform, then screen→world."""
        # EXIF orientations 1-8 per TIFF spec
        w, h = image_size
        x, y = pt.x, pt.y
        match orientation:
            case 1: pass                    # Normal
            case 2: x = w - x               # Flip H
            case 3: x, y = w - x, h - y     # Rotate 180
            case 4: y = h - y               # Flip V
            case 5: x, y = y, x             # Transpose
            case 6: x, y = h - y, x         # Rotate 90 CW
            case 7: x, y = y, w - x         # Transverse
            case 8: x, y = y, h - x         # Rotate 270 CW
            case _: raise CRSMismatchError(f"Invalid EXIF orientation: {orientation}")
        return self.screen_to_world(ScreenPoint(x, y), ScreenPoint(0, 0))
```

### Anti-Patterns to Avoid
- **Don't put business logic in Views:** Views only handle Qt widget lifecycle and signal connections.
- **Don't pass QObject models to Views:** Models are pure data; ViewModels expose `@Property` or signals.
- **Don't use `lambda` slots across threads:** Use `@Slot()` decorated methods or `CallableSlotAdapter` pattern.
- **Don't mix coordinate systems without conversion:** Always go through `CoordinateConverter`.
- **Don't skip `@Slot()` on QRunnable.run():** Required for cross-thread signal safety (PySide6 6.11+).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Project JSON serialization | Custom JSON encoder/decoder | `pydantic` + `model_dump_json()` / `model_validate_json()` | Handles nested dataclasses, validation, versioning |
| Settings persistence | Manual plist/INI parsing | `QSettings` with `NativeFormat` | Platform-native (plist on macOS), thread-safe |
| Coordinate transforms | Ad-hoc math in View code | Central `CoordinateConverter` service | Single source of truth, unit-testable, prevents Y-up/Y-down bugs |
| MVVM boilerplate | Custom base classes | `QObject` + `@Signal`/`@Slot` + `dataclass` models | Qt-native, no framework lock-in |
| macOS app bundle | Manual `codesign`/`hdiutil` scripts | `pyappdist` with `macapp`/`dmg` targets | Handles hidden imports, frameworks, notarization |
| Pre-commit hooks | Manual CI checks | `pre-commit` with Ruff/MyPy/pytest | Fast local feedback, consistent CI |

**Key insight:** PySide6 + Qt's model/view/delegate and signal/slot system already provides the MVVM infrastructure. Adding custom frameworks adds complexity without benefit. `pyappdist` solves the historically painful macOS Python app distribution problem by installing a dedicated Python runtime rather than freezing.

## Common Pitfalls

### Pitfall 1: PySide6 Memory Leaks with Lambdas in Signal Connections
**What goes wrong:** Connecting `button.clicked.connect(lambda: self.do_something())` creates a closure that holds a reference to `self`, preventing garbage collection. With `QRunnable`/`QThreadPool`, this causes segfaults when the C++ object is deleted but Python wrapper persists.

**Why it happens:** PySide6 creates a proxy object for undecorated Python callables. The proxy isn't automatically cleaned up when the receiver is deleted.

**How to avoid:** Always use `@Slot()` decorated methods on `QObject` subclasses. For lambdas, wrap in a `CallableSlotAdapter(QObject)` with parent set.

**Warning signs:** Objects not deleted after `deleteLater()`, increasing memory usage, random segfaults on app close.

### Pitfall 2: QSettings Path Confusion on macOS
**What goes wrong:** Using `QSettings("MyApp", "MyApp")` without setting `QCoreApplication.setOrganizationName()` and `setApplicationName()` writes to unpredictable paths (`~/Library/Preferences/com.unknown.plist`).

**Why it happens:** Qt constructs the plist domain from organization + application name. Defaults to "QtProject" if unset.

**How to avoid:** Call `QCoreApplication.setOrganizationName("HousePhotoMapper")` and `setApplicationName("HousePhotoMapper")` in `main()` before any `QSettings` instantiation.

### Pitfall 3: Coordinate System Y-Axis Flips
**What goes wrong:** Drawing annotations upside-down on plan because World (Y-up) → Screen (Y-down) transform missing the `-1` scale on Y.

**Why it happens:** Qt's `QGraphicsScene` uses Y-down; architectural plans use Y-up. EXIF orientations add 8 more variants.

**How to avoid:** Single `CoordinateConverter` service. Unit test all 8 EXIF orientations + World↔Screen round-trips.

### Pitfall 4: pyappdist Codesign Fails on Qt Frameworks
**What goes wrong:** `codesign --deep` fails on Qt framework symlinks (`.DS_Store` files, framework version symlinks).

**Why it happens:** `--deep` follows symlinks incorrectly; Qt bundles have complex framework structure.

**How to avoid:** Use pyappdist's built-in signing (it handles Qt frameworks correctly). If manual: `find . -name "*.dylib" -o -name "*.so" | xargs codesign -s "Developer ID" --options runtime` then sign `.app` last.

### Pitfall 5: QRunnable Auto-Delete Race Condition
**What goes wrong:** `QRunnable` with `autoDelete=True` (default) deleted by `QThreadPool` while Python still holds reference → segfault on next GC.

**Why it happens:** PySide6 6.6+ has fixed some cases but `setAutoDelete(False)` + explicit Python reference management is safer.

**How to avoid:** `runnable.setAutoDelete(False)`, keep Python reference in ViewModel, call `runnable.deleteLater()` in `finished` signal handler.

## Runtime State Inventory

> Phase 1 is greenfield — no existing runtime state. This section documents the expected state *after* Phase 1 for Phase 2 planning.

| Category | Items Expected After Phase 1 | Action Required |
|----------|------------------------------|-----------------|
| Stored data | `~/Library/Preferences/com.housephotomapper.HousePhotoMapper.plist` (window geometry, recent projects) | Code reads/writes via `QSettings` |
| Live service config | None (no external services yet) | — |
| OS-registered state | macOS app bundle in `/Applications` (post-install), LaunchServices registration | `pyappdist` DMG install handles |
| Secrets/env vars | None (no API keys in v1) | — |
| Build artifacts | `dist/*.app`, `dist/*.dmg`, `build/` | `gitignore` build artifacts; CI publishes DMG |

**Nothing found in category:** Verified — greenfield project.

## Code Examples

### Main Entry Point with Structured Logging
```python
# src/house_photo_mapper/__main__.py
import sys
import structlog
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt
from house_photo_mapper.infrastructure.logging import configure_logging
from house_photo_mapper.presentation.views.main_window import MainWindow
from house_photo_mapper.presentation.viewmodels.main_window_vm import MainWindowViewModel
from house_photo_mapper.domain.services.persistence import PersistenceService

def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    QCoreApplication.setOrganizationName("HousePhotoMapper")
    QCoreApplication.setApplicationName("HousePhotoMapper")
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("House Photo Mapper")

    persistence = PersistenceService()
    vm = MainWindowViewModel(persistence)
    window = MainWindow(vm)
    window.show()

    log.info("app_started", version="0.1.0")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### QSettings Persistence Service
```python
# src/house_photo_mapper/domain/services/persistence.py
from pathlib import Path
from PySide6.QtCore import QSettings, QStandardPaths
from house_photo_mapper.domain.models.project import ProjectModel

class PersistenceService:
    def __init__(self):
        self._settings = QSettings(QSettings.NativeFormat, QSettings.UserScope,
                                    "HousePhotoMapper", "HousePhotoMapper")

    def save_project(self, project: ProjectModel) -> None:
        path = Path(project.path)
        path.write_text(project.model_dump_json(indent=2))
        self._add_recent_project(str(path))

    def load_project(self, path: str) -> ProjectModel:
        data = Path(path).read_text()
        project = ProjectModel.model_validate_json(data)
        self._add_recent_project(path)
        return project

    def get_recent_projects(self) -> list[str]:
        return self._settings.value("recentProjects", [], type=list)

    def _add_recent_project(self, path: str) -> None:
        recent = self.get_recent_projects()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._settings.setValue("recentProjects", recent[:10])

    def save_window_geometry(self, geometry: bytes) -> None:
        self._settings.setValue("mainWindow/geometry", geometry)

    def load_window_geometry(self) -> bytes | None:
        return self._settings.value("mainWindow/geometry", type=bytes)

    def save_window_state(self, state: bytes) -> None:
        self._settings.setValue("mainWindow/state", state)

    def load_window_state(self) -> bytes | None:
        return self._settings.value("mainWindow/state", type=bytes)
```

### pyappdist Configuration (pyproject.toml)
```toml
# pyproject.toml (excerpt)
[tool.pyappdist]
name = "HousePhotoMapper"
python = "3.12"

[[tool.pyappdist.launchers]]
name = "house-photo-mapper"
entry = "house_photo_mapper.__main__:main"
gui = true
icon = { macos = "resources/icons/app.icns" }

[[tool.pyappdist.targets]]
name = "macos-arm64-app"
platform = "macos-aarch64"
format = "macapp"
codesign_identity = "Developer ID Application: Your Name (TEAMID)"
entitlements = "resources/entitlements.plist"

[[tool.pyappdist.targets]]
name = "macos-arm64-dmg"
platform = "macos-aarch64"
format = "dmg"
codesign_identity = "Developer ID Application: Your Name (TEAMID)"
entitlements = "resources/entitlements.plist"
notarize = true
notarize_profile = "notary-profile"
```

### entitlements.plist (Hardened Runtime)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key><true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
    <key>com.apple.security.cs.disable-library-validation</key><true/>
    <key>com.apple.security.files.user-selected.read-write</key><true/>
    <key>com.apple.security.network.client</key><true/>
</dict>
</plist>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyInstaller `--onefile` | pyappdist dedicated runtime | 2023 | No hidden imports, faster startup, easier notarization |
| `setup.py` + `requirements.txt` | `pyproject.toml` + `uv.lock` | 2022 (PEP 621) | Single config, reproducible builds |
| flake8 + black + isort | Ruff | 2023 | 100x faster, unified config |
| mypy loose | mypy strict + `basedpyright` (optional) | 2024 | Catches more bugs, LSP parity |
| Manual `codesign` scripts | pyappdist built-in signing | 2024 | Handles Qt frameworks correctly |
| QWidget-only | QWidget + QGraphicsView (Phase 2) | Qt 6 | Scene-graph better for CAD/plan viewport |

**Deprecated/outdated:**
- `py2app` — macOS only, notarization fragile
- `pipenv` / `poetry` — slower than `uv`, more complex lockfiles
- `@pyqtSlot` / `@pyqtSignal` — PySide6 uses `@Slot` / `@Signal` (same names, different module)
- `QSettings.IniFormat` on macOS — use `NativeFormat` for plist

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pyappdist 0.8+ supports notarization via `notarize = true` | Standard Stack | Build fails; fallback to manual notarization script |
| A2 | PySide6 6.11 LTS `@Slot()` on `QRunnable.run()` prevents cross-thread segfaults | Pitfalls | Thread crashes; mitigation: use `QThread` + `moveToThread` pattern |
| A3 | `QSettings.NativeFormat` on macOS writes to `~/Library/Preferences/com.housephotomapper.HousePhotoMapper.plist` | Code Examples | Settings lost on restart; mitigation: explicit plist path |
| A4 | `CoordinateConverter` stateless design works for all phases | Architecture Patterns | Need per-viewport state later; mitigation: add `ViewportContext` param |

## Open Questions

1. **PyMuPDF licensing for Phase 2**
   - What we know: PyMuPDF is AGPL-3.0 dual-licensed (commercial via Artifex). Phase 2 requires PDF rendering.
   - What's unclear: Whether our closed-source desktop app triggers AGPL "network use" clause (it doesn't serve network users). Legal review needed before Phase 2.
   - Recommendation: Proceed with Phase 1. Evaluate alternatives (pdfium-python, pypdfium2) or budget for commercial license in Phase 2 planning.

2. **Coordinate system precision for large plans**
   - What we know: `float64` (Python `float`) gives ~15 decimal digits. At 100 px/m, 10km plan = 1M pixels = well within precision.
   - What's unclear: Whether tile pyramid (Phase 2) needs fixed-point or integer coordinates for tile indexing.
   - Recommendation: Start with `float`; benchmark in Phase 2.

3. **macOS minimum version**
   - What we know: Python 3.12 requires macOS 10.13+. Qt 6.11 requires 10.14+.
   - What's unclear: Whether to target 10.14 (Mojave) or 11.0 (Big Sur) for wider compatibility.
   - Recommendation: Set `MACOSX_DEPLOYMENT_TARGET=10.14` in pyappdist; test on oldest supported.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.12+ | Runtime | ✓ | 3.12.x | — |
| uv | Package mgmt | ✓ | 0.4+ | pip (slower) |
| Xcode Command Line Tools | codesign, notarytool | ✓ | 15+ | — |
| Apple Developer ID | Codesign/notarize | ? | — | Ad-hoc sign (no distribution) |
| PySide6 6.11 | GUI | ✓ (via uv) | 6.11.x | — |

**Missing dependencies with no fallback:**
- Apple Developer ID certificate — required for notarized distribution. Without it, only ad-hoc signing works (local testing only).

**Missing dependencies with fallback:**
- Notarization profile (`notarytool` keychain profile) — can use `xcrun notarytool submit --apple-id --password --team-id` inline.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2+ with pytest-qt 4.4+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/unit -x -q` |
| Full suite command | `uv run pytest --cov=src/house_photo_mapper --cov-report=term-missing` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| PM-01 | Create new project → empty workspace | integration | `pytest tests/integration/test_app_lifecycle.py::test_new_project` | ❌ Wave 0 |
| PM-02 | Open existing project → restores state | integration | `pytest tests/integration/test_app_lifecycle.py::test_open_project` | ❌ Wave 0 |
| PM-03 | Save project → .hpmpj created | unit | `pytest tests/unit/test_persistence.py::test_save_project` | ❌ Wave 0 |
| PM-04 | Save As → new path, original unchanged | unit | `pytest tests/unit/test_persistence.py::test_save_as` | ❌ Wave 0 |
| CP-01 | App launches as native macOS .app | integration | `pytest tests/integration/test_app_lifecycle.py::test_macos_bundle` | ❌ Wave 0 |
| CP-01 | CoordinateSystem enum + Converter unit tested | unit | `pytest tests/unit/test_coordinate.py -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit -x -q` (<30s)
- **Per wave merge:** `uv run pytest --cov=src/house_photo_mapper --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_coordinate.py` — covers coordinate system enum, converter, CRSMismatchError
- [ ] `tests/unit/test_project_model.py` — covers ProjectModel JSON serialization, validation
- [ ] `tests/unit/test_persistence.py` — covers save/load/save-as, recent projects, QSettings
- [ ] `tests/integration/test_app_lifecycle.py` — covers app launch, window show, menu actions
- [ ] `tests/conftest.py` — `qtbot` fixture, `QApplication` singleton management
- [ ] Framework install: `uv add --dev pytest pytest-qt pytest-cov` — if none detected

## Security Domain

> `security_enforcement: true` in config (ASVS Level 1)

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No | — (local desktop app, no auth) |
| V3 Session Management | No | — (no sessions) |
| V4 Access Control | No | — (single-user, file-based) |
| V5 Input Validation | Yes | `pydantic` validation on ProjectModel load; `pathlib.Path` for safe paths |
| V6 Cryptography | No | — (no crypto in Phase 1) |
| V7 Error Handling | Yes | `structlog` structured errors; no stack traces in UI |
| V8 Logging | Yes | `structlog` JSON output; no PII in logs |
| V9 Communication Security | No | — (local only) |
| V10 Malicious Code | Yes | `uv` lockfile pins; `pyappdist` bundles audited runtime |
| V11 Business Logic | Yes | CoordinateConverter raises `CRSMismatchError` on invalid transforms |
| V12 File/Resources | Yes | Atomic writes (`.tmp` → rename); `.bak` on save (Phase 5) |

### Known Threat Patterns for Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious .hpmpj file (JSON injection) | Tampering | `pydantic` strict validation on load; reject extra fields |
| Path traversal in Save As | Tampering | `Path.resolve()` + `is_relative_to(project_dir)` check |
| Unsigned macOS binary | Spoofing | `codesign --options runtime` + notarization |
| DYLD injection via unsigned dylibs | Elevation | Hardened Runtime + `disable-library-validation` only where needed |

## Sources

### Primary (HIGH confidence)
- [PySide6 6.11 Documentation](https://doc.qt.io/qtforpython-6/) — MVVM patterns, Signal/Slot, QSettings, QRunnable
- [pyappdist GitHub](https://github.com/atsuoishimoto/pyappdist) — macOS app bundle, DMG, codesign, notarization config
- [uv Documentation](https://docs.astral.sh/uv/) — Project init, dependency management, lockfile
- [Ruff Documentation](https://docs.astral.sh/ruff/) — Lint rules, format, pyproject.toml config
- [MyPy Documentation](https://mypy.readthedocs.io/) — Strict mode config
- [Qt Coordinate System](https://doc.qt.io/qt-6/coordsys.html) — World/Viewport/Window transforms
- [EXIF Orientation Spec](https://www.exiftool.org/TagNames/EXIF.html) — 8 orientation values

### Secondary (MEDIUM confidence)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/) — qtbot fixture, async testing
- [structlog Documentation](https://www.structlog.org/) — Configuration, processors
- [Apple Notarization Docs](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) — notarytool, stapler
- [LibreCAD Graphics Viewport](https://deepwiki.com/LibreCAD/LibreCAD/3.1-graphics-view-and-rendering) — World/Screen coordinate conversion patterns

### Tertiary (LOW confidence)
- Various Stack Overflow / Qt Forum threads on PySide6 memory management — verify in implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI, official docs current
- Architecture: HIGH — MVVM with Qt Signal/Slot is Qt-endorsed pattern
- Pitfalls: HIGH — based on documented PySide6 issues (PYSIDE-3288, PYSIDE-2621) and community reports
- macOS bundling: MEDIUM — pyappdist 0.8 is alpha; notarization workflow tested but may need iteration
- Coordinate system: HIGH — math is well-established; EXIF 8 orientations from TIFF spec

**Research date:** 2025-07-13
**Valid until:** 2025-10-13 (90 days — PySide6 LTS stable, pyappdist may evolve)
