"""Main application entry point and lifecycle management."""

import sys
from typing import NoReturn

from PySide6.QtWidgets import QApplication

from house_photo_mapper.domain.services.persistence import PersistenceService
from house_photo_mapper.infrastructure.logging import configure_logging
from house_photo_mapper.presentation.viewmodels.main_window_vm import MainWindowViewModel
from house_photo_mapper.presentation.views.main_window import MainWindow


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

    persistence = PersistenceService()
    vm = MainWindowViewModel(persistence)
    window = MainWindow(vm, persistence)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
