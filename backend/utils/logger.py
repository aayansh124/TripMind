"""Centralized logging configuration."""

import logging
import os
import re
import sys
from typing import Optional

# Secret patterns to mask from logs
SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key[\s:=]+)([A-Za-z0-9_\-]{8,})", re.IGNORECASE),
    re.compile(r"(password[\s:=]+)([^\s,]+)", re.IGNORECASE),
    re.compile(r"(secret[\s:=]+)([^\s,]+)", re.IGNORECASE),
    re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)", re.IGNORECASE),
]


class SanitizingFormatter(logging.Formatter):
    """Custom formatter to redact sensitive credentials from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SECRET_PATTERNS:
            if "postgres" in pattern.pattern:
                sanitized = pattern.sub(r"\1***\3", sanitized)
            else:
                sanitized = pattern.sub(r"\1***", sanitized)
        return sanitized


def setup_logger(
    name: str = "travel_planner",
    log_level: Optional[str] = None,
    log_to_file: bool = True
) -> logging.Logger:
    """Initialize and configure a named logger.

    Args:
        name: Name of the logger.
        log_level: Log level string (INFO, DEBUG, etc.). Defaults to INFO or settings.
        log_to_file: Whether to attach a file handler under logs/ directory.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    level_name = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    logger.propagate = False

    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = SanitizingFormatter(fmt=fmt, datefmt=datefmt)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "travel_planner.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # Fall back to console only if file creation fails
            pass

    return logger


# Default application logger
logger = setup_logger("travel_planner")

