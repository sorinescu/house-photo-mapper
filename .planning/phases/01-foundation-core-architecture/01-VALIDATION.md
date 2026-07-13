---
phase: 1
slug: foundation-core-architecture
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2025-07-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.2+ with pytest-qt 4.4+ |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/unit -x -q` |
| **Full suite command** | `uv run pytest --cov=src/house_photo_mapper --cov-report=term-missing` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit -x -q`
- **After every plan wave:** Run `uv run pytest --cov=src/house_photo_mapper --cov-report=term-missing`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01 | 01 | 1 | PM-01 | T-1-01 | ProjectModel validates JSON on create/load; Path traversal prevented | unit | `uv run pytest tests/unit/test_project_model.py -v` | ❌ W0 | ⬜ pending |
| 01-02 | 01 | 1 | PM-02, PM-03 | T-1-02 | Atomic write (`.tmp` → rename); `pydantic` validation on load | unit | `uv run pytest tests/unit/test_persistence.py::test_save_project -v` | ❌ W0 | ⬜ pending |
| 01-03 | 01 | 1 | PM-04 | T-1-02 | Save As writes to new path; original unchanged; `Path.resolve()` check | unit | `uv run pytest tests/unit/test_persistence.py::test_save_as -v` | ❌ W0 | ⬜ pending |
| 01-04 | 01 | 1 | CP-01 (coords) | T-1-03 | `CRSMismatchError` raised on invalid transforms; all 8 EXIF orientations tested | unit | `uv run pytest tests/unit/test_coordinate.py -v` | ❌ W0 | ⬜ pending |
| 01-05 | 01 | 1 | CP-01 (bundle) | T-1-04 | App bundle codesigned with Hardened Runtime; `codesign --verify --deep` passes | integration | `uv run pytest tests/integration/test_app_lifecycle.py::test_macos_bundle -v` | ❌ W0 | ⬜ pending |
| 01-06 | 01 | 1 | PM-01, PM-02 | T-1-05 | QApplication singleton; MainWindow shows; menu actions wired to VM slots | integration | `uv run pytest tests/integration/test_app_lifecycle.py::test_new_project -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_coordinate.py` — covers coordinate system enum, converter, CRSMismatchError
- [ ] `tests/unit/test_project_model.py` — covers ProjectModel JSON serialization, validation
- [ ] `tests/unit/test_persistence.py` — covers save/load/save-as, recent projects, QSettings
- [ ] `tests/integration/test_app_lifecycle.py` — covers app launch, window show, menu actions
- [ ] `tests/conftest.py` — `qtbot` fixture, `QApplication` singleton management
- [ ] Framework install: `uv add --dev pytest pytest-qt pytest-cov` — if none detected

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| macOS .app bundle launches from Finder | CP-01 | Requires built .app artifact; CI cannot GUI test | Build DMG via `uv run pyappdist build macos-arm64-dmg`, install, launch from Applications folder |
| Window geometry persists across sessions | PM-02 | Requires app restart; QSettings read at startup | Open app, move/resize window, quit, reopen — verify position/size restored |
| Recent projects menu populates | PM-02 | Requires multiple save/load cycles | Save 3 projects, reopen app — verify "File > Open Recent" lists them |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending