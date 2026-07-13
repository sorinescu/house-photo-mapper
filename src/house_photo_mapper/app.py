"""Main application entry point and lifecycle management."""

import sys
from typing import NoReturn

from PySide6.QtWidgets import QApplication, QMainWindow

from house_photo_mapper.infrastructure.logging import configure_logging


def _create_placeholder_window() -> QMainWindow:
    """Create a placeholder MainWindow for scaffolding phase."""
    window = QMainWindow()
    window.setWindowTitle("HousePhotoMapper (Scaffolding)")
    window.resize(800, 600)
    return window


def create_application() -> QApplication:
    """Create and configure the QApplication instance."""
    app = QApplication(sys.argv)
    app.setApplicationName("HousePhotoMapper")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("HousePhotoMapper")
    app.setOrganizationDomain("housephotomapper.app")
    return app


def main() -> NoReturn:
    """Application entry point."""
    configure_logging()
    app = create_application()

    # Import here to avoid circular imports
    # MainWindow is implemented in Plan 01-02; use a placeholder for scaffolding
    try:
        from house_photo_mapper.presentation.views.main_window import (
            MainWindow,  # type: ignore[import-not-found]
        )

        window = MainWindow()
    except ImportError:
        window = _create_placeholder_window()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
