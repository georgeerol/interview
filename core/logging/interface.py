"""
Logger Interface

Abstract interface defining logging operations for business search application.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Logger(ABC):
    """Abstract base class for logging operations with structured metadata support."""
    
    @abstractmethod
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log informational message.
        
        Args:
            message: Log message text
            extra: Optional structured metadata dictionary
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log warning message.
        
        Args:
            message: Warning message text
            extra: Optional structured metadata dictionary
        """
        pass
    
    @abstractmethod
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False) -> None:
        """
        Log error message.
        
        Args:
            message: Error message text
            extra: Optional structured metadata dictionary
            exc_info: Whether to include exception traceback information
        """
        pass
