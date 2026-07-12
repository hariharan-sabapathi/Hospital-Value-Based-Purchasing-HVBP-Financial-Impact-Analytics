"""
logger.py

Provides a single get_logger() factory so every module logs consistently
to both console and a rotating log file, configured via config.yaml.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(
    name: str,
    log_file: Path,
    level: str = "INFO",
    max_bytes: int = 1_048_576,
    backup_count: int = 3,
) -> logging.Logger:
    """Create (or fetch) a logger with console + rotating file handlers."""
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured (e.g., called from multiple modules in one run).
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
