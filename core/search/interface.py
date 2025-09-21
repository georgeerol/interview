"""
Business Search Service Interface

Abstract interface defining core business search operations with
multi-modal filtering and radius expansion capabilities.
"""
from abc import ABC, abstractmethod

from .value_objects import SearchParams, SearchResult


class BusinessSearchService(ABC):
    """
    Abstract base class for business search operations.
    
    Defines the contract for implementing business search with support for
    state filtering, geospatial search, text search, and radius expansion.
    """
    
    @abstractmethod
    def search(self, params: SearchParams) -> SearchResult:
        """
        Perform business search with multi-modal filtering and radius expansion.
        
        Supports state-based filtering, geospatial search with intelligent
        radius expansion, and text-based name filtering. Combines multiple
        location types using OR logic.
        
        Args:
            params: Search parameters containing locations, radius, and text filters
            
        Returns:
            SearchResult with businesses, metadata, and operation details
        """
        pass
