"""
Metrics Service Interface

Abstract interface for performance monitoring and metrics following SOLID principles.
"""
from abc import ABC, abstractmethod
from django.http import HttpRequest

from ..search import SearchResult


class MetricsService(ABC):
    """Interface for performance monitoring and metrics."""
    
    @abstractmethod
    def start_tracking(self, request: HttpRequest) -> str:
        """Start performance tracking and return search ID."""
        pass
    
    @abstractmethod
    def log_success(self, search_id: str, result: SearchResult) -> None:
        """Log successful search completion."""
        pass
    
    @abstractmethod
    def get_processing_time(self, search_id: str) -> float:
        """Get processing time for a search ID."""
        pass
