import logging
import sys

logger = logging.getLogger(__name__)


def configure_logger(level: int) -> None:
    """Configure the logger for this module."""
    logger.setLevel(level)
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
