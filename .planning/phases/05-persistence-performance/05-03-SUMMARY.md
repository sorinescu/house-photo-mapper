---
phase: 05-persistence-performance
plan: 03
subsystem: infrastructure
tags: [crash-recovery, bak-files, data-integrity, qt-dialog]

# Dependency graph
requires:
  - phase: 04-photo-management
    provides: PhotoModel, photo persistence
  - phase: 05-persistence-performance/02
    provides: PersistenceService, atomic writes, .bak backup creation
provides:
  - RecoveryScanner for .bak file discovery
  - RecoveryDialog for user recovery selection
  - recover_project() method for validated recovery
  - Data integrity validation on project load
affects: [05-persistence-performance]

# Tech tracking
tech-stack:
  added: []
  patterns: [recovery-scanner, qt-dialog-with-table, data-validation]

key-files:
  created:
    - src/house_photo_mapper/infrastructure/recovery.py
    - src/house_photo_mapper/presentation/views/recovery_dialog.py
  modified:
    - src/house_photo_mapper/domain/services/persistence.py
    - src/house_photo_mapper/presentation/views/main_window.py

key-decisions:
  - "Recovery scans app data dir + recent project parent dirs"
  - "24-hour cutoff for recoverable .bak files"
  - "7-day automatic cleanup of old .bak files"
  - "Validation runs on both normal load and recovery"

patterns-established:
  - "RecoveryScanner pattern: scan dirs, inspect files, return dataclasses"
  - "Qt dialog with QTableWidget for multi-select data display"
  - "Data validation with warning collection pattern"

requirements-completed: [NFR-Reliability]

# Coverage metadata
coverage:
  - id: D1
    description: RecoveryScanner discovers .bak files from app data and recent project directories"
    verification:
      - kind: unit
        ref: "tests/test_recovery.py#test_scanner_finds_bak_files"
        status: pass
    human_judgment: false
  - id: D2
    description: "RecoveryDialog displays recoverable projects with preview data"
    verification: []
    human_judgment: true
    rationale: "Qt dialog rendering requires visual verification"
  - id: D3
    description: "recover_project validates data and logs recovery operations"
    verification:
      - kind: unit
        ref: "tests/test_recovery.py#test_recover_project_validation"
        status: pass
    human_judgment: false
  - id: D4
    description: "Application scans for .bak files on startup and shows recovery dialog"
    verification: []
    human_judgment: true
    rationale: "Integration with MainWindow requires runtime testing"
  - id: D5
    description: "Data integrity checks validate annotation references and required fields"
    verification:
      - kind: unit
        ref: "tests/test_recovery.py#test_data_integrity_checks"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 3: Crash Recovery Summary

**Crash recovery with .bak file scanning, recovery dialog, and data integrity validation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-15T05:46:44Z
- **Completed:** 2026-07-15T05:50:09Z
- **Tasks:** 5
- **Files modified:** 4

## Accomplishments
- RecoveryScanner discovers .bak files from app data and recent project directories
- RecoveryDialog shows recoverable projects with timestamps and preview data
- recover_project() validates recovered data with logging
- Data integrity checks validate annotation references and required fields
- Automatic cleanup of old .bak files (> 7 days) on startup

## Task Commits

Each task was committed atomically:

1. **Task 1: Create RecoveryScanner** - `08da248` (feat)
2. **Task 2: Create RecoveryDialog** - `0e842bd` (feat)
3. **Task 3: Implement Recovery Logic** - `13eb331` (feat)
4. **Task 4: Wire to Application Startup** - `b490669` (feat)
5. **Task 5: Add Data Integrity Checks** - `89b52fa` (feat)

## Files Created/Modified
- `src/house_photo_mapper/infrastructure/recovery.py` - RecoveryScanner and RecoverableProject dataclass
- `src/house_photo_mapper/presentation/views/recovery_dialog.py` - Qt dialog for recovery selection
- `src/house_photo_mapper/domain/services/persistence.py` - Added recover_project() and data validation
- `src/house_photo_mapper/presentation/views/main_window.py` - Wired recovery scan to startup

## Decisions Made
- Recovery scans app data dir + recent project parent directories
- 24-hour cutoff for recoverable .bak files (configurable)
- 7-day automatic cleanup of old .bak files
- Validation runs on both normal load and recovery for consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Crash recovery infrastructure complete
- Ready for integration with auto-save system
- Data integrity validation in place for future phases

---
*Phase: 05-persistence-performance*
*Completed: 2026-07-15*
