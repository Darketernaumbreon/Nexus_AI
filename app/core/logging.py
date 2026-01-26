import logging
import sys
import structlog
from typing import Any

def configure_logger():
    """
    Configure structlog for JSON output and standard logging bridge.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> Any:
    """
    Returns a structlog logger.
    """
    return structlog.get_logger(name)

# Initialize configuration on import
configure_logger()
print("Structlog configured.")
