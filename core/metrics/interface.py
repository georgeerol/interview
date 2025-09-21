"""
Metrics Service Interface

Abstract interface defining performance monitoring and metrics operations
for business search tracking.
"""
from abc import ABC, abstractmethod
from django.http import HttpRequest

from ..search import SearchResult


class MetricsService(ABC):
    """Abstract base class for performance monitoring and search metrics tracking."""
    
    @abstractmethod
    def start_tracking(self, request: HttpRequest) -> str:
        """
        Start performance tracking for a search request.
        
        Args:
            request: HTTP request object to track
            
        Returns:
            Unique search ID string for tracking this request
        """
        pass
    
    @abstractmethod
    def log_success(self, search_id: str, result: SearchResult) -> None:
        """
        Log successful completion of a search operation.
        
        Args:
            search_id: Unique search ID from start_tracking
            result: Search result object containing operation details
        """
        pass
    
    @abstractmethod
    def get_processing_time(self, search_id: str) -> float:
        """
        Get processing time for a completed search operation.
        
        Args:
            search_id: Unique search ID from start_tracking
            
        Returns:
            Processing time in milliseconds
        """
        pass
