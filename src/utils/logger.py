import logging

from src.config.paths import LOG_DIR
from src.config.settings import LOG_LEVEL

LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str):
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # File handler
        file_handler = logging.FileHandler(LOG_DIR / "pipeline.log")
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
