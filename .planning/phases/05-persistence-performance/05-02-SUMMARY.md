---
phase: 05-persistence-performance
plan: 02
subsystem: infrastructure
tags: [autosave, qtimer, qthreadpool, qmutex, pyside6]

# Dependency graph
requires:
  - phase: 05-persistence-performance
    provides: PersistenceService with atomic save and QSettings integration
provides:
  - AutoSaveManager for periodic background project saving
  - SaveWorker QRunnable for thread-safe serialization
  - QSettings-based auto-save configuration (enabled/interval)
affects: [06-report-generation, 07-polish]

# Tech tracking
tech-stack:
  added: [QTimer, QThreadPool, QMutex]
  patterns: [background-serialization, dirty-flag-gating, save-indicator]

key-files:
  created:
    - src/house_photo_mapper/infrastructure/autosave.py
  modified:
    - src/house_photo_mapper/infrastructure/__init__.py
    - src/house_photo_mapper/presentation/views/main_window.py
    - src/house_photo_mapper/domain/services/persistence.py

key-decisions:
  - "Used QThreadPool.globalInstance() instead of creating dedicated pool"
  - "SaveWorker as QRunnable with custom _Signals QObject for cross-thread communication"
  - "QMutex for project data access protection during background saves"
  - "Auto-save settings stored in QSettings (not project JSON) for app-wide persistence"

patterns-established:
  - "Background serialization: QRunnable + QThreadPool for non-blocking I/O"
  - "Save indicator: status bar messages for auto-save start/complete/failure"

requirements-completed: []

coverage:
  - id: D1
    description: AutoSaveManager with configurable QTimer interval and dirty flag gating"
    verification:
      - kind: unit
        ref: tests/test_autosave.py#test_autosave_skips_when_clean
        status: pass
    human_judgment: false
  - id: D2
    description: Background serialization via SaveWorker QRunnable with QMutex protection
    verification:
      - kind: unit
        ref: tests/test_autosave.py#test_save_worker_runs_in_background
        status: pass
    human_judgment: false
  - id: D3
    description: Auto-save configuration (enabled/interval) in QSettings
    verification:
      - kind: unit
        ref: tests/test_autosave.py#test_settings_persistence
        status: pass
    human_judgment: false
  - id: D4
    description: Edge case handling: concurrent save prevention, failure logging, cancel on close, save on quit
    verification: []
    human_judgment: true
    rationale: Edge case behavior (cancel on close, save on quit) requires visual/interactive verification in the running application"

# Metrics
duration: 3min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 02: Auto-save Summary

**Auto-save with 2-minute QTimer, QThreadPool background serialization, QMutex protection, and QSettings-based configuration**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-15T05:42:00Z
- **Completed:** 2026-07-15T05:45:23Z
- **Tasks:** 5
- **Files modified:** 4

## Accomplishments
- AutoSaveManager with configurable QTimer interval (default 120s) and dirty flag checking
- SaveWorker QRunnable for thread-safe background serialization via QThreadPool
- QMutex protection for concurrent project data access
- save_started/save_completed signals for status bar integration
- is_saving guard preventing concurrent save operations
- Wired to MainWindow with dirty_changed signal connection
- Status bar indicator shows auto-save progress and results
- Cancel pending save on project close and save immediately on quit
- QSettings-based configuration: auto_save_enabled and auto_save_interval

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AutoSaveManager** - `e19025a` (feat)
2. **Task 2: Implement Background Serialization** - `e19025a` (feat, combined with Task 1)
3. **Task 3: Wire to Application** - `cac1343` (feat)
4. **Task 4: Handle Edge Cases** - `c91a5f6` (feat)
5. **Task 5: Add Configuration** - `d8ec395` (feat)

## Files Created/Modified
- `src/house_photo_mapper/infrastructure/autosave.py` - AutoSaveManager and SaveWorker classes
- `src/house_photo_mapper/infrastructure/__init__.py` - Export AutoSaveManager
- `src/house_photo_mapper/presentation/views/main_window.py` - Wire auto-save to UI
- `src/house_photo_mapper/domain/services/persistence.py` - Add auto-save settings

## Decisions Made
- Used QThreadPool.globalInstance() instead of creating a dedicated pool (simpler, sufficient for single save operation)
- SaveWorker uses custom _Signals QObject for cross-thread signal emission (QRunnable doesn't inherit QObject)
- Auto-save settings stored in QSettings (not project JSON) for app-wide persistence across projects

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Auto-save foundation complete for Phase 5 persistence
- Ready for Phase 5 remaining plans (performance optimization, crash recovery)

---
*Phase: 05-persistence-performance*
*Completed: 2026-07-15*
