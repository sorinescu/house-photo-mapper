---
phase: 05-persistence-performance
plan: 01
subsystem: persistence
tags: [json, schema-versioning, atomic-write, backup, streaming, pydantic]

# Dependency graph
requires:
  - phase: 04-annotation-tools
    provides: AnnotationModel and project CRUD pipeline
provides:
  - Versioned project JSON schema (schema_version field)
  - .bak file management for crash recovery
  - Schema version validation and migration framework
  - Streaming serialization for 1000+ photos
  - Enhanced ExportSettings with report layout/margins
  - Auto-save on window close
affects: [06-report-generation, 07-testing-polish]

# Tech tracking
tech-stack:
  added: [project_schema.py, streaming_serializer.py]
  patterns: [atomic-write-tmp-rename, bak-backup, schema-versioning, chunked-json]

key-files:
  created:
    - src/house_photo_mapper/domain/models/project_schema.py
    - src/house_photo_mapper/domain/services/streaming_serializer.py
  modified:
    - src/house_photo_mapper/domain/models/project.py
    - src/house_photo_mapper/domain/models/__init__.py
    - src/house_photo_mapper/domain/services/persistence.py
    - src/house_photo_mapper/domain/services/__init__.py
    - src/house_photo_mapper/presentation/views/main_window.py

key-decisions:
  - "Schema version field on ProjectModel enables forward/backward compatibility"
  - ".bak files created on save when target exists (crash recovery)"
  - "Streaming serialization uses chunked writes (500 items/chunk) to avoid memory spikes"
  - "Auto-save on window close prevents data loss"

patterns-established:
  - "Atomic write: write to .tmp, rename to final (same filesystem)"
  - "Schema versioning: SCHEMA_VERSION constant + validate_schema_version() + migrate_schema()"
  - "Chunked JSON serialization for large arrays"

requirements-completed: [FR-9]

coverage:
  - id: D1
    description: "Versioned project JSON schema with schema_version field"
    requirement: "FR-9"
    verification:
      - kind: unit
        ref: "tests/test_persistence.py#test_plan_model_persistence"
        status: pass
      - kind: automated_ui
        ref: "python -c 'from house_photo_mapper.domain.models.project import ProjectModel; p=ProjectModel(); assert p.schema_version==1'"
        status: pass
    human_judgment: false
  - id: D2
    description: ".bak file management for crash recovery"
    requirement: "FR-9"
    verification:
      - kind: automated_ui
        ref: "python -c verifies .bak created on second save"
        status: pass
    human_judgment: false
  - id: D3
    description: "Streaming serialization for 1000+ photos without memory spike"
    requirement: "NFR-Perf"
    verification:
      - kind: automated_ui
        ref: "python -c verifies 1000 photos serialized in 148 KB"
        status: pass
    human_judgment: false
  - id: D4
    description: "Auto-save on window close and status bar save indicator"
    requirement: "NFR-Reliability"
    verification: []
    human_judgment: true
    rationale: "Requires visual verification of Qt widget behavior in running app"

# Metrics
duration: 4min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 01: PersistenceService Summary

**Versioned project schema with .bak backups, streaming serialization for 1000+ photos, and auto-save on close**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-15T05:35:19Z
- **Completed:** 2026-07-15T05:40:09Z
- **Tasks:** 5
- **Files modified:** 7

## Accomplishments
- Created versioned project JSON schema (project_schema.py) with SCHEMA_VERSION, validation, and migration framework
- Enhanced PersistenceService with .bak file management and schema version checking on load
- Implemented streaming serializer for chunked JSON writes handling 1000+ photos (148 KB for 1000 items)
- Added report layout, margins, and figure numbering to ExportSettings
- Wired MainWindow to auto-save on close and show status bar save indicator

## Task Commits

Each task was committed atomically:

1. **Task 1: Design Project JSON Schema** - `9d574a6` (feat)
2. **Task 2: Enhance PersistenceService** - `01e18b5` (feat)
3. **Task 3: Implement Streaming Serialization** - `eefa98f` (feat)
4. **Task 4: Update ProjectModel** - `9c2840a` (feat)
5. **Task 5: Wire to MainWindow** - `91e8db1` (feat)

## Files Created/Modified
- `src/house_photo_mapper/domain/models/project_schema.py` - Schema versioning, validation, migration framework
- `src/house_photo_mapper/domain/services/streaming_serializer.py` - Chunked JSON writes for large arrays
- `src/house_photo_mapper/domain/models/project.py` - Added schema_version, ui_state, enhanced ExportSettings
- `src/house_photo_mapper/domain/models/__init__.py` - Export new schema classes
- `src/house_photo_mapper/domain/services/persistence.py` - .bak management, schema version checks, backup loading
- `src/house_photo_mapper/domain/services/__init__.py` - Export streaming serializer functions
- `src/house_photo_mapper/presentation/views/main_window.py` - Auto-save on close, status bar indicator

## Decisions Made
- Schema version field on ProjectModel enables forward/backward compatibility checks on load
- .bak files created on save only when target exists (avoids unnecessary backup on first save)
- Streaming serialization uses 500-item chunks to balance memory usage and file readability
- Auto-save on window close prevents accidental data loss

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Persistence foundation complete for Phase 6 (report generation)
- Schema versioning ready for future format changes
- Streaming serialization handles large photo collections efficiently

---
*Phase: 05-persistence-performance*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 7 key files exist on disk. All 5 task commits verified in git log.
