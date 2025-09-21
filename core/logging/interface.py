"""
Logger Interface

Abstract interface for logging operations following SOLID principles.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Logger(ABC):
    """Interface for logging operations."""
    
    @abstractmethod
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False) -> None:
        """Log error message."""
        pass
