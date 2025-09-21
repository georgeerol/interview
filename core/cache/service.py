"""
Cache Service Implementation

Django cache implementation following SOLID principles.
"""
import hashlib
import json
from typing import Dict, Any, Optional
from django.core.cache import cache

from .interface import CacheService


class DjangoCacheService(CacheService):
    """
    Django cache implementation.
    
    Single Responsibility: Handle caching operations only.
    """
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key."""
        return cache.get(key)
    
    def set(self, key: str, value: Dict[str, Any], timeout: int) -> None:
        """Set cached value with timeout."""
        cache.set(key, value, timeout)
    
    def generate_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from request data."""
        # Create a normalized version of the request for consistent caching
        normalized_data = {
            'locations': sorted(data.get('locations', []), key=str),
            'radius_miles': data.get('radius_miles'),
            'text': data.get('text', '').strip().lower()
        }
        
        # Create hash of the normalized request
        data_str = json.dumps(normalized_data, sort_keys=True)
        cache_key = f"business_search:{hashlib.md5(data_str.encode()).hexdigest()}"
        return cache_key
