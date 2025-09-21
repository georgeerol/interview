"""
Core Interfaces Package

Abstract interfaces for dependency inversion following SOLID principles.
All concrete implementations depend on these abstractions.
"""

from .interfaces import (
    # Value Objects
    SearchParams,
    SearchResult,
    
    # Service Interfaces
    BusinessSearchService,
    CacheService,
    MetricsService,
    ResponseBuilder,
    Logger,
)

__all__ = [
    # Value Objects
    "SearchParams",
    "SearchResult",
    
    # Service Interfaces  
    "BusinessSearchService",
    "CacheService",
    "MetricsService",
    "ResponseBuilder",
    "Logger",
]
