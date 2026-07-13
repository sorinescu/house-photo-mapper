# Technology Stack

**Project:** HousePhotoMapper
**Researched:** 2025-07-13
**Overall Confidence:** HIGH

---

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Python** | 3.12+ | Primary language | LTS until 2028, excellent ecosystem, modern typing |
| **PySide6** | 6.11+ | Cross-platform desktop framework | Official Qt for Python (LGPL), Qt 6.11 LTS, mature, no commercial license needed for proprietary apps |
| **Qt** | 6.11 LTS | Underlying C++ framework | Long-term support until 2026-11, stable API |

**Confidence:** HIGH — PySide6 is the industry standard for professional Python desktop apps in 2025. Qt 6.11 LTS provides stability. LGPL allows closed-source distribution without fees.

**Not PyQt6:** GPL license requires commercial license ($4,200/dev/year) for proprietary apps. PySide6 LGPL permits dynamic linking without fees.

**Not Tkinter/wxPython/Kivy:** Lack professional widget set, model/view architecture, and accessibility for complex documentation apps.

---

### PDF Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PyMuPDF (fitz)** | 1.24+ | PDF rendering, text extraction, page manipulation | 10x faster than pdfplumber, renders pages to images for plan display, supports annotations/forms, AGPL but commercial license available |
| **ReportLab** | 4.3+ | Professional PDF report generation | Canvas-based, pixel-perfect control, industry standard for complex reports, pure Python |
| **fpdf2** | 2.7+ | Simple PDF generation fallback | Lightweight, pure Python, easier API for basic reports |

**Confidence:** HIGH — PyMuPDF is undisputed performance leader for PDF rendering/extraction. ReportLab remains gold standard for programmatic PDF generation with precise layout control.

**License Note:** PyMuPDF is AGPL-3.0. For commercial distribution, either: (a) purchase Artifex commercial license, (b) open-source the app, or (c) isolate PyMuPDF in a separate process communicating via IPC. For this project, evaluate commercial license cost vs. open-source strategy.

**Not pdfplumber:** 10x slower, no PDF generation, MIT license but inadequate for 100+ page plan rendering.

**Not WeasyPrint:** Requires system dependencies (Pango/Cairo), slower for data-driven reports, better suited for HTML-to-PDF.

**Not PyPDF2/pypdf:** No rendering capability, only manipulation.

---

### Image Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pillow** | 11.1+ | Core image loading, thumbnails, EXIF, format conversion | Pure Python API, 30+ formats, standard library for image I/O, MIT license |
| **pillow-heif** | 1.4+ | HEIC/HEIF support via libheif | Pillow plugin, registers HEIF opener automatically, BSD-3-Clause, actively maintained |
| **OpenCV (optional)** | 4.11+ | Computer vision features (future AI room detection) | Only if needed for advanced image analysis; adds 50MB+ dependency |

**Confidence:** HIGH — Pillow is the de facto standard. pillow-heif is the recommended HEIC solution (replaces deprecated pyheif). Pillow-SIMD not recommended: platform-specific, often outdated, maintenance burden.

**Not Pillow-SIMD:** Linux-only wheels, AVX2/SSE4 compilation complexity, often lags upstream Pillow by months, cross-platform deployment nightmare.

**Not imageio/scikit-image:** Overkill for basic thumbnail/EXIF needs.

---

### Desktop App Packaging & Distribution

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PyInstaller** | 6.13+ | Primary bundler for development/internal builds | Fastest build time (~22s), largest hook ecosystem, mature, PySide6 hooks built-in, cross-platform |
| **cx_Freeze** | 8.5+ | Alternative for faster startup on large apps | Directory-based builds start ~8s vs ~50s for PyInstaller onefile, native MSI/DMG/AppImage generators |
| **pyappdist** | 0.8+ | Native installer generation (MSI, MSIX, DMG, .run) | One pyproject.toml → native installers per platform, notarization support, WiX-based MSI |
| **ux** | 0.1+ | Cross-compilation & notarization from any host | Build macOS .app/.dmg with notarization from Linux CI, single binary distribution |

**Confidence:** HIGH — PyInstaller remains pragmatic default. cx_Freeze for startup-sensitive apps. pyappdist/ux for production native installers.

**Not Nuitka:** 4x slower builds, compiler dependency complexity, overkill unless runtime performance is critical (not for this UI-bound app).

**Not Briefcase:** Requires BeeWare ecosystem, mobile-focused.

**Distribution Strategy:**
- **macOS:** pyappdist/ux → .dmg with codesign + notarization (required for Gatekeeper on Catalina+)
- **Windows:** pyappdist → .msi (per-user) or .msix (Store/sideloading), code-signed with EV certificate
- **Linux:** pyappdist/ux → self-extracting .run installer + AppImage for portable use

---

### Dependency Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **uv** | 0.5+ | Package resolution, virtualenv, Python management | 10-20x faster than pip/Poetry, replaces pyenv+pip+venv+pip-tools, Rust-based, PEP-621 compliant |
| **pyproject.toml** | — | Project metadata & dependencies | Standard (PEP 621), tool-agnostic |

**Confidence:** HIGH — uv has become the 2025 default. Cold install ~8s vs ~90s for pip. Drop-in `uv pip` compatibility for migration.

**Not Poetry:** Slower resolver (Python-based), no Python version management, proprietary lockfile.
**Not PDM:** Squeezed by uv on PEP-621 axis, PEP 582 `__pypackages__` non-standard.
**Not pip-tools:** Manual compilation step, no environment management.

---

### Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | 8.3+ | Test framework | Industry standard, fixtures, parametrization |
| **pytest-qt** | 4.4+ | Qt widget testing | qtbot fixture for user simulation, waitSignal, headless CI support, auto-detects PySide6 |
| **pytest-cov** | 5.0+ | Coverage reporting | Standard |

**Confidence:** HIGH — pytest-qt is the established Qt testing plugin. Supports PySide6/PyQt6/PyQt5. Headless testing via xvfb on CI.

---

### Code Quality

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Ruff** | 0.12+ | Linting + formatting | 10-100x faster than Flake8+Black+isort, single tool, Black-compatible formatter, built-in import sorting (I rules), type rules (TCH), security (S) |
| **MyPy** | 1.16+ | Static type checking | Only tool for type-aware analysis, catches bugs Ruff misses |
| **pre-commit** | 4.0+ | Git hooks | Runs Ruff + MyPy on commit |

**Confidence:** HIGH — Ruff is the 2025 default for new projects. Consolidates 5+ tools. MyPy remains essential for type safety.

**Not Black+Flake8+isort:** Fragmented, slower, more config. Ruff's formatter is 99% Black-compatible.
**Not Pylint:** Slow, Ruff covers most Pylint rules (PL prefix).

---

### Configuration & Settings

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pydantic Settings** | 2.12+ | Application configuration (env vars, .env, validation) | Type-safe, validation, SecretStr for secrets, IDE autocomplete, .env support, FastAPI ecosystem |
| **QSettings** | Qt 6.11 | Persistent UI state (window geometry, recent files, preferences) | Native platform storage (registry/plist/INI), zero config, cross-platform |
| **appdirs** | 1.4+ | Cross-platform data directories | Locates platform-appropriate config/cache/data dirs |

**Confidence:** HIGH — Pydantic Settings for typed app config with validation. QSettings for UI persistence (native, no schema needed). appdirs for locating data directories.

**Not dynaconf:** Overkill for desktop app (designed for multi-env microservices). Hot-reload not needed.
**Not python-dotenv alone:** No validation, no type casting.

---

### Logging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **structlog** | 25.1+ | Structured application logging | Processor pipeline, contextvars for async context propagation, native JSONRenderer, OpenTelemetry integration, stdlib bridge for third-party logs |
| **standard logging** | stdlib | Bridge for library logs | structlog routes stdlib records via ProcessorFormatter |

**Confidence:** HIGH — structlog is the production standard for structured logging. ~25% faster JSON serialization than Loguru. Composability essential for debugging complex annotation workflows.

**Not Loguru:** Better DX for small scripts, but no processor pipeline, slower JSON, weaker stdlib integration.
**Not stdlib alone:** No structured fields, manual context propagation.

---

### Undo/Redo Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **QUndoStack + QUndoCommand** | Qt 6.11 | Unlimited undo/redo for annotations | Native Qt command pattern, mergeWith() for move compression, QUndoView for history panel, createUndoAction()/createRedoAction() for menus |

**Confidence:** HIGH — Qt's undo framework is battle-tested, integrates with QGraphicsScene, supports command macros and compression. Implement commands at model level (not view) for correctness.

---

### Auto-Update

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **tufup** | 0.10+ | Secure cross-platform updates | Built on python-tuf (The Update Framework), replaces archived PyUpdater, packaging-agnostic (works with PyInstaller/cx_Freeze/Nuitka), TUF security |
| **SparkleHelper** | 0.1+ | Native macOS Sparkle + Windows WinSparkle | Native update UI on each platform, EdDSA signing, integrates with Nuitka/PyInstaller |

**Confidence:** MEDIUM — tufup is active (v0.10 Oct 2025) while PyUpdater is archived. SparkleHelper provides native UX. Evaluate tufup maturity for production.

**Not PyUpdater:** Archived, unmaintained.
**Not esky:** Abandoned.

---

### EXIF Metadata

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **piexif** | 1.1+ | Read/write EXIF in JPEG/WebP/TIFF | Pure Python, simple API, works with Pillow, supports GPS, DateTime, orientation |
| **exifread** | 3.5+ | Read-only EXIF extraction (fallback) | Pure Python, supports HEIC/RAW, lighter if write not needed |

**Confidence:** HIGH — piexif is the standard for read/write. Combine with Pillow for orientation correction.

---

### Performance Optimization (1000+ photos, 100+ plan pages)

| Technique | Library/Implementation |
|-----------|------------------------|
| **Tile-based rendering** | Custom QGraphicsItem proxy pattern: load tiles on-demand, unload off-screen |
| **Viewport culling** | Only render visible tiles (QPane architecture) |
| **Threaded pyramids** | Background workers generate downsampled tiers for zoom-out |
| **Bit-blit scrolling** | Shift pixel buffer, render only damage strips |
| **Lazy thumbnail loading** | QAbstractListModel with canFetchMore/fetchMore for photo browser |
| **Draft mode JPEG** | `Image.draft()` for fast low-res preview |
| **Memory budget** | psutil-based auto cache sizing (leave 10% headroom) |

**Confidence:** HIGH — QPane (open-source, GPLv3) demonstrates production patterns. Qt Mandelbrot example shows threaded tiling.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GUI Framework | PySide6 | PyQt6 | GPL license cost for proprietary app |
| GUI Framework | PySide6 | Tkinter | Inadequate widgets, no model/view, poor accessibility |
| GUI Framework | PySide6 | wxPython | Smaller ecosystem, no QML, less maintained |
| PDF Rendering | PyMuPDF | pdfplumber | 10x slower, no rendering, no annotations |
| PDF Generation | ReportLab | WeasyPrint | System deps (Cairo/Pango), HTML-to-PDF not needed |
| PDF Generation | ReportLab | fpdf2 | Less powerful for complex architectural reports |
| Image Processing | Pillow | Pillow-SIMD | Linux-only, outdated, deployment complexity |
| HEIC Support | pillow-heif | pyheif | Deprecated, read-only, CFFI complexity |
| Packaging | PyInstaller | Nuitka | 4x slower builds, compiler deps, overkill |
| Packaging | PyInstaller | cx_Freeze | Smaller hook ecosystem (use cx_Freeze for fast startup only) |
| Dependency Mgmt | uv | Poetry | Slower, no Python management, proprietary lockfile |
| Dependency Mgmt | uv | PDM | Squeezed by uv, PEP 582 non-standard |
| Linting | Ruff | Black+Flake8+isort | Fragmented, slower, more config |
| Config | Pydantic Settings | dynaconf | Overkill for desktop app |
| Logging | structlog | Loguru | No processor pipeline, slower JSON |
| Auto-Update | tufup | PyUpdater | Archived, unmaintained |
| EXIF | piexif | PyExifTool | Requires external exiftool binary |

---

## Installation

```bash
# Core dependencies
uv add pyside6 pymupdf reportlab fpdf2 pillow pillow-heif piexif exifread

# Configuration & settings
uv add pydantic-settings appdirs

# Logging
uv add structlog

# Auto-update (evaluate tufup maturity first)
uv add tufup sparklehelper

# Development dependencies
uv add --dev pytest pytest-qt pytest-cov ruff mypy pre-commit pyinstaller cx_freeze pyappdist ux

# Optional: OpenCV for future AI features
# uv add opencv-python
```

---

## Version Pinning Strategy

```toml
# pyproject.toml [project]
dependencies = [
    "pyside6>=6.11,<6.12",      # Qt 6.11 LTS
    "pymupdf>=1.24,<1.25",      # Pin major for AGPL license review
    "reportlab>=4.3,<5.0",
    "fpdf2>=2.7,<3.0",
    "pillow>=11.1,<12.0",
    "pillow-heif>=1.4,<2.0",
    "piexif>=1.1,<2.0",
    "exifread>=3.5,<4.0",
    "pydantic-settings>=2.12,<3.0",
    "appdirs>=1.4,<2.0",
    "structlog>=25.1,<26.0",
    "tufup>=0.10,<1.0",
    "sparklehelper>=0.1,<1.0",
]

# uv.lock will pin exact transitive versions
```

---

## Sources

- Qt for Python / PySide6 official documentation (doc.qt.io)
- PyMuPDF benchmarks vs pdfplumber (pdfmux.com/blog, 2026)
- Pillow Performance benchmarks (python-pillow.github.io)
- Pillow-SIMD upstreaming PR #8209 (github.com/python-pillow/Pillow)
- uv benchmarks vs Poetry/PDM/pip (techplained.com, pydevtools.com, 2026)
- pytest-qt documentation (pytest-qt.readthedocs.io)
- Ruff vs Black/Flake8 comparison (docs.astral.sh, tenthirtyam.org, 2026)
- Pydantic Settings vs dynaconf (leapcell.io, dasroot.net, 2025-2026)
- PyInstaller vs Nuitka vs cx_Freeze empirical comparison (x321.org, 2025)
- Qt Undo Framework documentation (doc.qt.io/qt-6/qundo.html)
- tufup / PyUpdater status (github.com/dennisvang/tufup, pypi.org)
- SparkleHelper for native updates (pypi.org/project/SparkleHelper)
- structlog vs Loguru benchmarks (dash0.com, python-observability.com, 2026)
- EXIF libraries comparison (piexif.readthedocs.io, exifread on PyPI)
- pillow-heif for HEIC support (pypi.org/project/pillow-heif, github.com/bigcat88/pillow_heif)
- pyappdist for native installers (pypi.org/project/pyappdist)
- ux for cross-compilation/notarization (github.com/i2y/ux)
- QPane high-performance image viewer (github.com/Artificial-Sweetener/QPane)

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Core Framework | HIGH | PySide6/Qt 6.11 LTS is industry standard |
| PDF Processing | HIGH | PyMuPDF performance verified; ReportLab maturity verified |
| Image Processing | HIGH | Pillow + pillow-heif actively maintained |
| Packaging | HIGH | PyInstaller default; pyappdist/ux for production installers |
| Dependency Mgmt | HIGH | uv 1.0+ production adoption (Anthropic, Stripe) |
| Testing | HIGH | pytest-qt established, headless CI proven |
| Code Quality | HIGH | Ruff default for new projects 2025+ |
| Configuration | HIGH | Pydantic Settings + QSettings complementary roles |
| Logging | HIGH | structlog production standard for structured logging |
| Undo/Redo | HIGH | Qt framework native, well-documented |
| Auto-Update | MEDIUM | tufup active but younger; evaluate for production |
| EXIF/HEIC | HIGH | piexif + pillow-heif are current standards |
| Performance | HIGH | QPane demonstrates patterns; Qt examples exist |
