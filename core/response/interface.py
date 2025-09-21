"""
Response Builder Interface

Abstract interface defining API response construction operations
for business search endpoints.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from rest_framework.response import Response

from ..search import SearchResult


class ResponseBuilder(ABC):
    """Abstract base class for constructing structured API responses with metadata."""
    
    @abstractmethod
    def build_success_response(self, result: SearchResult, search_id: str, 
                             cached: bool = False, cache_key: str = None) -> Dict[str, Any]:
        """
        Build successful search response with comprehensive metadata.
        
        Args:
            result: Search result object containing businesses and operation details
            search_id: Unique search identifier for tracking
            cached: Whether the response was served from cache
            cache_key: Cache key used if response was cached
            
        Returns:
            Dictionary containing 'results' and 'search_metadata' keys
        """
        pass
    
    @abstractmethod
    def build_validation_error_response(self, errors: Dict[str, Any], 
                                      search_id: str) -> Response:
        """
        Build validation error response for invalid input.
        
        Args:
            errors: Validation error details from serializer
            search_id: Unique search identifier for tracking
            
        Returns:
            HTTP 400 Response with error details
        """
        pass
    
    @abstractmethod
    def build_server_error_response(self, error: Exception, 
                                  search_id: str) -> Response:
        """
        Build server error response for unexpected exceptions.
        
        Args:
            error: Exception that occurred during processing
            search_id: Unique search identifier for tracking
            
        Returns:
            HTTP 500 Response with error message and search ID
        """
        pass
