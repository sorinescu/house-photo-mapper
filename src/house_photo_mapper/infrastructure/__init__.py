"""Infrastructure package."""

from house_photo_mapper.infrastructure.logging import bind_context, configure_logging, get_logger
from house_photo_mapper.infrastructure.platform import (
    get_app_data_dir,
    get_app_version,
    is_apple_silicon,
    is_macos,
    open_file_externally,
    set_dock_icon,
)
from house_photo_mapper.infrastructure.qt_patterns import (
    CallableSlotAdapter,
    QtSafeRunnable,
    QtSafeViewModel,
    safe_connect,
)

__all__ = [
    "configure_logging",
    "get_logger",
    "bind_context",
    "is_macos",
    "is_apple_silicon",
    "get_app_version",
    "set_dock_icon",
    "get_app_data_dir",
    "open_file_externally",
    "CallableSlotAdapter",
    "QtSafeRunnable",
    "QtSafeViewModel",
    "safe_connect",
]
