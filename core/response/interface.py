"""
Response Builder Interface

Abstract interface for building API responses following SOLID principles.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from rest_framework.response import Response

from ..search import SearchResult


class ResponseBuilder(ABC):
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
