"""
Business Search Service Interface

Abstract interface for business search operations following SOLID principles.
"""
from abc import ABC, abstractmethod

from .value_objects import SearchParams, SearchResult


class BusinessSearchService(ABC):
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
