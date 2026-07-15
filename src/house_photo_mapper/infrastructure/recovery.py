"""RecoveryScanner - Scans for .bak files and provides crash recovery data.

Scans the application data directory and project directories for .bak backup
files created by PersistenceService during atomic saves. Returns structured
recovery information including timestamps and project previews.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Maximum age for .bak files to be considered recoverable (24 hours)
MAX_BAK_AGE_HOURS = 24

# Maximum age for .bak files before automatic cleanup (7 days)
CLEANUP_AGE_DAYS = 7


@dataclass
class RecoverableProject:
    """Information about a recoverable project from a .bak file."""

    bak_path: Path
    original_path: Path
    project_name: str
    modified_at: datetime
    photo_count: int = 0
    annotation_count: int = 0
    plan_count: int = 0
    file_size_bytes: int = 0
    parse_errors: list[str] = field(default_factory=list)


class RecoveryScanner:
    """Scans for .bak files and provides crash recovery data.

    The scanner looks for .hpmpj.bak files in:
    1. The application data directory
    2. Recently used project directories (from recent projects list)

    Features:
    - Timestamp-based filtering (only recent saves)
    - Data preview (photo/annotation/plan counts)
    - Graceful handling of corrupted .bak files
    - Cleanup of old .bak files (> 7 days)
    """

    def __init__(
        self,
        app_data_dir: Path | None = None,
        recent_projects: list[str] | None = None,
        max_age_hours: int = MAX_BAK_AGE_HOURS,
        cleanup_age_days: int = CLEANUP_AGE_DAYS,
    ) -> None:
        """Initialize RecoveryScanner.

        Args:
            app_data_dir: Application data directory to scan.
            recent_projects: List of recent project paths to scan parent dirs.
            max_age_hours: Maximum age in hours for .bak files to be recoverable.
            cleanup_age_days: Age in days before .bak files are cleaned up.
        """
        self._app_data_dir = app_data_dir
        self._recent_projects = recent_projects or []
        self._max_age_hours = max_age_hours
        self._cleanup_age_days = cleanup_age_days

    def scan_for_recoverable(self) -> list[RecoverableProject]:
        """Scan for recoverable .bak files.

        Returns:
            List of RecoverableProject instances, sorted by modified_at (newest first).
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self._max_age_hours)
        seen_paths: set[Path] = set()
        results: list[RecoverableProject] = []

        # Scan directories for .bak files
        scan_dirs = self._get_scan_directories()
        for scan_dir in scan_dirs:
            if not scan_dir.is_dir():
                continue
            for bak_path in scan_dir.glob("*.hpmpj.bak"):
                if bak_path in seen_paths:
                    continue
                seen_paths.add(bak_path)

                project = self._inspect_bak_file(bak_path, now)
                if project is None:
                    continue

                # Only include if within age cutoff
                if project.modified_at >= cutoff:
                    results.append(project)
                else:
                    logger.debug(
                        "Skipping old .bak: %s (modified %s)",
                        bak_path,
                        project.modified_at,
                    )

        # Sort by modification time (newest first)
        results.sort(key=lambda p: p.modified_at, reverse=True)

        logger.info(
            "Found %d recoverable project(s) from %d scanned directory(s)",
            len(results),
            len(scan_dirs),
        )
        return results

    def cleanup_old_backups(self) -> int:
        """Remove .bak files older than cleanup_age_days.

        Returns:
            Number of .bak files removed.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self._cleanup_age_days)
        removed = 0

        scan_dirs = self._get_scan_directories()
        for scan_dir in scan_dirs:
            if not scan_dir.is_dir():
                continue
            for bak_path in scan_dir.glob("*.hpmpj.bak"):
                try:
                    stat = bak_path.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        bak_path.unlink()
                        removed += 1
                        logger.info("Removed old .bak: %s", bak_path)
                except OSError as e:
                    logger.warning("Failed to remove .bak %s: %s", bak_path, e)

        if removed > 0:
            logger.info("Cleaned up %d old .bak file(s)", removed)
        return removed

    def _get_scan_directories(self) -> list[Path]:
        """Get list of directories to scan for .bak files.

        Returns:
            List of directory paths to scan.
        """
        dirs: list[Path] = []

        # Application data directory
        if self._app_data_dir is not None:
            dirs.append(self._app_data_dir)

        # Parent directories of recent projects
        for project_path in self._recent_projects:
            parent = Path(project_path).parent
            if parent.is_dir() and parent not in dirs:
                dirs.append(parent)

        return dirs

    def _inspect_bak_file(
        self, bak_path: Path, now: datetime
    ) -> RecoverableProject | None:
        """Inspect a .bak file and extract recovery metadata.

        Args:
            bak_path: Path to the .bak file.
            now: Current time for age calculations.

        Returns:
            RecoverableProject if the file is valid, None otherwise.
        """
        try:
            stat = bak_path.stat()
        except OSError as e:
            logger.warning("Cannot stat .bak file %s: %s", bak_path, e)
            return None

        # Derive original project path
        original_path = Path(str(bak_path).replace(".hpmpj.bak", ".hpmpj"))
        project_name = original_path.stem

        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        # Try to parse the .bak file for preview data
        photo_count = 0
        annotation_count = 0
        plan_count = 0
        parse_errors: list[str] = []

        try:
            raw_data = json.loads(bak_path.read_text())
            photo_count = len(raw_data.get("photos", []))
            annotation_count = len(raw_data.get("annotations", []))
            plan_count = len(raw_data.get("plans", []))
        except (json.JSONDecodeError, OSError) as e:
            parse_errors.append(f"Failed to parse .bak: {e}")
            logger.warning("Failed to parse .bak %s: %s", bak_path, e)

        return RecoverableProject(
            bak_path=bak_path,
            original_path=original_path,
            project_name=project_name,
            modified_at=modified_at,
            photo_count=photo_count,
            annotation_count=annotation_count,
            plan_count=plan_count,
            file_size_bytes=stat.st_size,
            parse_errors=parse_errors,
        )
