"""
Cache Service Interface

Abstract interface defining caching operations for business search results.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CacheService(ABC):
    """Abstract base class for caching operations in business search."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached value by key.
        
        Args:
            key: Cache key string
            
        Returns:
            Cached data dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], timeout: int) -> None:
        """
        Store value in cache with expiration timeout.
        
        Args:
            key: Cache key string
            value: Data to cache
            timeout: Expiration timeout in seconds
        """
        pass
    
    @abstractmethod
    def generate_key(self, data: Dict[str, Any]) -> str:
        """
        Generate unique cache key from search request data.
        
        Args:
            data: Search request data dictionary
            
        Returns:
            Unique cache key string
        """
        pass
