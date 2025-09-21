"""
Cache Service Implementation

Django-based caching service for business search results.
"""
import hashlib
import json
from typing import Dict, Any, Optional
from django.core.cache import cache

from .interface import CacheService


class DjangoCacheService(CacheService):
    """
    Django cache backend implementation for business search caching.
    
    Uses Django's cache framework to store and retrieve search results
    with MD5-based key generation for consistent caching.
    """
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached search results by key.
        
        Args:
            key: Cache key string
            
        Returns:
            Cached search results dictionary or None if not found
        """
        return cache.get(key)
    
    def set(self, key: str, value: Dict[str, Any], timeout: int) -> None:
        """
        Store search results in cache with expiration.
        
        Args:
            key: Cache key string
            value: Search results data to cache
            timeout: Cache expiration timeout in seconds
        """
        cache.set(key, value, timeout)
    
    def generate_key(self, data: Dict[str, Any]) -> str:
        """
        Generate unique cache key from search request data.
        
        Normalizes the request data (sorts locations, lowercases text) and
        creates an MD5 hash for consistent cache key generation.
        
        Args:
            data: Search request data dictionary
            
        Returns:
            Unique cache key string with 'business_search:' prefix
        """
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
