"""Project dialogs - File dialogs for New, Open, Save As operations."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QWidget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def new_project_dialog(parent: QWidget | None, directory: str) -> str | None:
    """Show New Project dialog and return selected path.

    Args:
        parent: Parent widget for the dialog.
        directory: Starting directory.

    Returns:
        Selected file path or None if cancelled.
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "New Project",
        str(Path(directory) / "Untitled.hpmpj"),
        "HousePhotoMapper Projects (*.hpmpj)",
    )
    return path if path else None


def open_project_dialog(parent: QWidget | None, directory: str) -> str | None:
    """Show Open Project dialog and return selected path.

    Args:
        parent: Parent widget for the dialog.
        directory: Starting directory.

    Returns:
        Selected file path or None if cancelled.
    """
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Open Project",
        directory,
        "HousePhotoMapper Projects (*.hpmpj)",
    )
    return path if path else None


def save_as_dialog(parent: QWidget | None, directory: str, default_name: str) -> str | None:
    """Show Save As dialog and return selected path.

    Args:
        parent: Parent widget for the dialog.
        directory: Starting directory.
        default_name: Default file name.

    Returns:
        Selected file path or None if cancelled.
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Project As",
        str(Path(directory) / default_name),
        "HousePhotoMapper Projects (*.hpmpj)",
    )
    return path if path else None
