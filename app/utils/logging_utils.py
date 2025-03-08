import logging
import sys
from typing import Any, Dict

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with a specific format and handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)

    return logger

def log_state(logger: logging.Logger, state: Dict[str, Any], prefix: str = "") -> None:
    """Log the current state of the workflow."""
    logger.debug(f"{prefix} State Contents:")
    for key, value in state.items():
        if value is not None:
            if isinstance(value, dict):
                logger.debug(f"{prefix} {key}:")
                for sub_key, sub_value in value.items():
                    logger.debug(f"{prefix}   {sub_key}: {type(sub_value)}")
            else:
                logger.debug(f"{prefix} {key}: {type(value)}") 