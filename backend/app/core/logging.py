"""Structured logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the root logger for METFI."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=level.upper(),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("metfi")
    return logger


logger = setup_logging()
