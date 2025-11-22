"""Logging configuration for the application."""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "learning_curator",
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """Set up application logger.
    
    Args:
        name: Logger name
        level: Logging level
        format_string: Custom format string
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # Create formatter
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(message)s'
        )
    
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str = "learning_curator") -> logging.Logger:
    """Get or create logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    # Configure root logger if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        from .config import get_config
        config = get_config()
        
        # Set root logger level
        numeric_level = getattr(logging, config.log_level.upper(), logging.INFO)
        root_logger.setLevel(numeric_level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        
        # Create formatter
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(message)s'
        )
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger.addHandler(handler)
    
    # Get the requested logger (will inherit from root)
    logger = logging.getLogger(name)
    
    return logger

