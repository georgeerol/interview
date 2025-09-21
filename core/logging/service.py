"""
Logger Service Implementation

Django logging implementation following SOLID principles.
"""
import logging
from typing import Dict, Any, Optional

from .interface import Logger


class DjangoLogger(Logger):
    """
    Django logging implementation.
    
    Single Responsibility: Handle logging operations only.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.logger.info(message, extra=extra or {})
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=extra or {})
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False) -> None:
        """Log error message."""
        self.logger.error(message, extra=extra or {}, exc_info=exc_info)
