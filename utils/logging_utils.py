import logging
from pathlib import Path
import os

from utils.file_utils import ensure_directory_exists
from config.settings import LOG_DIR


def setup_logger(name, log_file=None, level='INFO'):
    """Set up a logger with file and console handlers"""

    # Create logs directory relative to project root
    ensure_directory_exists(LOG_DIR)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_execution_time(func): # decorator
    pass