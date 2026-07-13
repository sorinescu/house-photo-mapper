"""Platform-specific utilities for HousePhotoMapper."""

import os
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from house_photo_mapper import __version__

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def is_macos() -> bool:
    """Return True if running on macOS."""
    return sys.platform == "darwin"


def is_apple_silicon() -> bool:
    """Return True if running on Apple Silicon (arm64)."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def get_app_version() -> str:
    """Return the application version."""
    return __version__


def set_dock_icon(app: "QApplication", icon_path: str | Path) -> None:
    """Set the Dock icon on macOS.

    Args:
        app: QApplication instance.
        icon_path: Path to .icns file.
    """
    if not is_macos():
        return
    try:
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))
    except Exception:
        pass  # Silently fail on non-macOS or if icon not found


def get_app_data_dir() -> Path:
    """Get the application data directory.

    Returns:
        Path to application data directory (~/Library/Application Support/HousePhotoMapper on macOS).
    """
    if is_macos():
        return Path.home() / "Library" / "Application Support" / "HousePhotoMapper"
    elif sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "HousePhotoMapper"
    else:
        return Path.home() / ".local" / "share" / "HousePhotoMapper"


def open_file_externally(path: Path) -> bool:
    """Open a file with the default system application.

    Args:
        path: Path to file to open.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if is_macos():
            import subprocess
            subprocess.run(["open", str(path)], check=False)
            return True
        elif sys.platform == "win32":
            os.startfile(path)  # type: ignore
            return True
        else:
            import subprocess
            subprocess.run(["xdg-open", str(path)], check=False)
            return True
    except Exception:
        return False
