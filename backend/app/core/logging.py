import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Log Format: Time | Level | Module | Message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"

def setup_logging():
    logger = logging.getLogger("ai_platform")
    logger.setLevel(logging.INFO)

    # Console Handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(stdout_handler)

    # File Handler (Rotating: Max 5MB per file, keep 5 backups)
    # Gracefully skip if directory creation fails (e.g. read-only filesystem on Render)
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=5*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
    except OSError:
        pass

    return logger

logger = setup_logging()
