"""
Logger Module

Centralized logging for all scrapers with formatted output and file handlers.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from utils.config import ScraperConfig


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with standardized configuration.

    Args:
        name: Logger name (usually module or component name)
        level: Log level (uses config default if None)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.hasHandlers():
        return logger

    log_level = level or ScraperConfig.log_level
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(name)-20s | %(levelname)-8s | "
            "%(filename)s:%(lineno)d | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)

    # File handler (detailed format)
    log_dir = Path(ScraperConfig.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=ScraperConfig.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create root logger
root_logger = get_logger("scraper")