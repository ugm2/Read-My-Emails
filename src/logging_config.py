import logging
import os

from rich.logging import RichHandler


def setup_logging(name: str, level: str = None) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name
        level: Optional logging level override (defaults to env var or WARNING)
        
    Returns:
        Configured logger instance
    """
    log_level = level or os.getenv("LOGGER_LEVEL", "WARNING").upper()
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            omit_repeated_times=False
        )
        
        formatter = logging.Formatter('%(name)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 