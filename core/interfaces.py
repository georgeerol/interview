"""
Business Search API Interfaces

Abstract interfaces following SOLID principles for dependency inversion.
All concrete implementations depend on these abstractions, not vice versa.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from django.http import HttpRequest
from rest_framework.response import Response

from .models import Business


@dataclass
class SearchParams:
    """Value object for search parameters."""
    locations: List[Dict[str, Any]]
    radius_miles: Optional[float] = None
    text: str = ""


@dataclass 
class SearchResult:
    """Value object for search results."""
    businesses: List[Business]
    total_found: int
    filters_applied: List[str]
    locations: List[Dict[str, Any]]
    geo_locations: List[Dict[str, Any]]
    radius_used: float
    radius_expanded: bool
    radii_tried: List[float]
    radius_miles: Optional[float]


class IBusinessSearchService(ABC):
    """Interface for business search operations."""
    
    @abstractmethod
    def search(self, params: SearchParams) -> SearchResult:
        """
        Perform business search based on provided parameters.
        
        Args:
            params: Search parameters including locations, radius, text
            
        Returns:
            SearchResult containing businesses and metadata
        """
        pass


class ICacheService(ABC):
    """Interface for caching operations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], timeout: int) -> None:
        """Set cached value with timeout."""
        pass
    
    @abstractmethod
    def generate_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from request data."""
        pass


class IMetricsService(ABC):
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


class IResponseBuilder(ABC):
    """Interface for building API responses."""
    
    @abstractmethod
    def build_success_response(self, result: SearchResult, search_id: str, 
                             cached: bool = False, cache_key: str = None) -> Dict[str, Any]:
        """Build successful search response with metadata."""
        pass
    
    @abstractmethod
    def build_validation_error_response(self, errors: Dict[str, Any], 
                                      search_id: str) -> Response:
        """Build validation error response."""
        pass
    
    @abstractmethod
    def build_server_error_response(self, error: Exception, 
                                  search_id: str) -> Response:
        """Build server error response."""
        pass


class ILogger(ABC):
    """Interface for logging operations."""
    
    @abstractmethod
    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, extra: Dict[str, Any] = None, 
              exc_info: bool = False) -> None:
        """Log error message."""
        pass
