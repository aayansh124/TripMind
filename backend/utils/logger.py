
"""Centralized logging configuration."""

import logging
import os
import re
import sys
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(
        r"(api[_-]?key[\s:=]+)([A-Za-z0-9_\-]{8,})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(password[\s:=]+)([^\s,]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(secret[\s:=]+)([^\s,]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)",
        re.IGNORECASE,
    ),
]


class SanitizingFormatter(logging.Formatter):
    """Redact sensitive credentials from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)

        for pattern in SECRET_PATTERNS:
            if "postgres" in pattern.pattern:
                formatted_message = pattern.sub(
                    r"\1***\3",
                    formatted_message,
                )
            else:
                formatted_message = pattern.sub(
                    r"\1***",
                    formatted_message,
                )

        return formatted_message


def setup_logger(
    name: str = "travel_planner",
    log_level: str | None = None,
    log_to_file: bool = True,
) -> logging.Logger:
    """Initialize and configure a named application logger."""

    application_logger = logging.getLogger(name)

    if application_logger.handlers:
        return application_logger

    level_name = (
        log_level or os.getenv("LOG_LEVEL", "INFO")
    ).upper()

    level = getattr(logging, level_name, logging.INFO)

    application_logger.setLevel(level)
    application_logger.propagate = False

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "[%(filename)s:%(lineno)d]: %(message)s"
    )

    formatter = SanitizingFormatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    application_logger.addHandler(console_handler)

    if log_to_file:
        try:
            project_root = Path(__file__).resolve().parents[2]
            log_directory = project_root / "logs"

            log_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            log_file = log_directory / "travel_planner.log"

            file_handler = logging.FileHandler(
                log_file,
                encoding="utf-8",
            )

            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            application_logger.addHandler(file_handler)

        except OSError:
            application_logger.warning(
                "File logging unavailable. Console logging remains active."
            )

    return application_logger


logger = setup_logger()
