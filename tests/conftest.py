"""Pytest configuration and fixtures for HousePhotoMapper tests."""

import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

# Ensure src is on the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for the entire test session.

    This fixture creates a single QApplication instance that is reused
    across all tests, which is required by Qt.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("HousePhotoMapper-Test")
        app.setOrganizationName("HousePhotoMapper-Test")
    yield app
    # QApplication cleanup is handled by Qt


@pytest.fixture
def qtbot(qapp: QApplication) -> Generator[QtBot, None, None]:
    """Create a QtBot instance for testing Qt widgets.

    This fixture provides a QtBot instance that can be used to interact
    with Qt widgets in tests (clicking, typing, waiting for signals, etc.).
    """
    bot = QtBot(qapp)
    yield bot


@pytest.fixture(autouse=True)
def _reset_logging() -> Generator[None, None, None]:
    """Reset logging configuration between tests to avoid interference."""
    import logging

    import structlog

    # Reset structlog
    structlog.configure(
        processors=[],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Reset root logger handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    yield

    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
