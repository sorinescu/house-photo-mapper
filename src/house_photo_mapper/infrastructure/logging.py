"""Structured logging configuration using structlog."""

import logging
import os
import sys
from typing import Any, cast

import structlog


def configure_logging(
    level: str | None = None,
    json_output: bool = True,
    stream: Any | None = None,
) -> None:
    """Configure structlog with JSON output and ISO timestamps.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var or INFO.
        json_output: Whether to output JSON (True) or console-friendly format (False).
        stream: Output stream. Defaults to sys.stderr.
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()

    log_level = getattr(logging, level, logging.INFO)

    if stream is None:
        stream = sys.stderr

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=stream,
        level=log_level,
    )

    # Reduce noise from PySide6
    logging.getLogger("PySide6").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name. Uses caller's module if not provided.

    Returns:
        Configured structlog logger.
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def bind_context(**kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Create a logger with bound context variables.

    Args:
        **kwargs: Key-value pairs to bind as context.

    Returns:
        Logger with bound context.
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger().bind(**kwargs))
