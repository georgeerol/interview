"""
Cache Service Interface

Abstract interface for caching operations following SOLID principles.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CacheService(ABC):
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
