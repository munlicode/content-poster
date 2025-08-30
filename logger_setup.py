import logging
from logging.handlers import RotatingFileHandler
import sys
import os


def setup_logger():
    """Configures a rotating log file for the application."""
    # Define the log file and rotation settings
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(project_root, "app.log")

    max_log_size_mb = 5  # Max size in MB before rotating
    backup_count = 5  # How many old log files to keep

    # Create logger
    logger = logging.getLogger("ContentPosterLogger")
    logger.setLevel(logging.INFO)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    # Create a rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_log_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding="utf-8",
    )

    # Create a formatter and set it for the handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger if they aren't already added
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger


# Create a single logger instance to be used across the application
log = setup_logger()
