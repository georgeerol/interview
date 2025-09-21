"""
Logger Service Implementation

Django-based logging service implementation for business search application.
"""
import logging
from typing import Dict, Any, Optional

from .interface import Logger


class DjangoLogger(Logger):
    """
    Django logging backend implementation.
    
    Uses Django's logging framework to provide structured logging
    with metadata support for business search operations.
    """
    
    def __init__(self):
        """Initialize Django logger instance."""
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log informational message with optional metadata.
        
        Args:
            message: Log message text
            extra: Optional structured metadata dictionary
        """
        self.logger.info(message, extra=extra or {})
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log warning message with optional metadata.
        
        Args:
            message: Warning message text
            extra: Optional structured metadata dictionary
        """
        self.logger.warning(message, extra=extra or {})
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False) -> None:
        """
        Log error message with optional metadata and exception info.
        
        Args:
            message: Error message text
            extra: Optional structured metadata dictionary
            exc_info: Whether to include exception traceback information
        """
        self.logger.error(message, extra=extra or {}, exc_info=exc_info)
