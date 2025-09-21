"""
Business Search API Services

Concrete implementations of the business search interfaces.
Each service has a single responsibility and depends only on abstractions.
"""
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from .interfaces import (
    IBusinessSearchService, ICacheService, IMetricsService, 
    IResponseBuilder, ILogger, SearchParams, SearchResult
)
from .models import Business
from .serializers import BusinessSerializer
from .utils import expand_radius_search_multiple_locations


class BusinessSearchService(IBusinessSearchService):
    """
    Core business search service.
    
    Single Responsibility: Handle business search logic only.
    No dependencies on HTTP, caching, or logging concerns.
    """
    
    def search(self, params: SearchParams) -> SearchResult:
        """Perform business search based on provided parameters."""
        # Initialize search state
        businesses = Business.objects.all()
        filters_applied = []
        
        # Apply text filtering if provided
        if params.text:
            businesses = businesses.filter(name__icontains=params.text)
            filters_applied.append("text")
        
        # Separate location types
        state_locations = [loc for loc in params.locations if "state" in loc]
        geo_locations = [loc for loc in params.locations if "lat" in loc and "lng" in loc]
        
        # Apply state filtering
        if state_locations:
            state_codes = [loc["state"] for loc in state_locations]
            businesses = businesses.filter(state__in=state_codes)
            filters_applied.append("state")
        
        # Handle geo-location filtering with radius expansion
        final_businesses = []
        radius_used = params.radius_miles if params.radius_miles is not None else 50.0
        radius_expanded = False
        radii_tried = []
        
        if geo_locations:
            filters_applied.append("geo")
            
            # Start with all businesses for geo filtering
            base_businesses = Business.objects.all()
            if params.text:
                base_businesses = base_businesses.filter(name__icontains=params.text)
            
            # Apply radius expansion for geo locations
            geo_businesses, radius_used, radius_expanded, radii_tried = expand_radius_search_multiple_locations(
                base_businesses, 
                geo_locations, 
                params.radius_miles
            )
            
            # Combine state-filtered and geo-filtered results (OR logic)
            if state_locations:
                state_businesses = list(businesses)  # Already filtered by state and text
                final_businesses = geo_businesses + state_businesses
            else:
                final_businesses = geo_businesses
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_businesses = []
            for business in final_businesses:
                if business.id not in seen_ids:
                    seen_ids.add(business.id)
                    unique_businesses.append(business)
            
            business_list = unique_businesses[:100]  # Limit to 100
        else:
            # No geo locations, use existing state/text filtered results
            business_list = list(businesses[:100])
        
        # Calculate total found for metadata
        total_found = len(final_businesses) if geo_locations else len(list(businesses))
        
        return SearchResult(
            businesses=business_list,
            total_found=total_found,
            filters_applied=filters_applied,
            locations=params.locations,
            geo_locations=geo_locations,
            radius_used=radius_used,
            radius_expanded=radius_expanded,
            radii_tried=radii_tried,
            radius_miles=params.radius_miles
        )


class DjangoCacheService(ICacheService):
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


class SearchMetricsService(IMetricsService):
    """
    Performance monitoring service.
    
    Single Responsibility: Handle performance tracking only.
    """
    
    def __init__(self, logger: ILogger):
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    def start_tracking(self, request) -> str:
        """Start performance tracking and return search ID."""
        start_time = time.time()
        search_id = f"search_{int(start_time * 1000)}"
        
        # Store start time for later use
        self._start_times[search_id] = start_time
        
        self.logger.info(f"[{search_id}] Business search started", extra={
            'search_id': search_id,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
        })
        
        return search_id
    
    def log_success(self, search_id: str, result: SearchResult) -> None:
        """Log successful search completion."""
        processing_time = self.get_processing_time(search_id)
        
        self.logger.info(f"[{search_id}] Search completed successfully", extra={
            'search_id': search_id,
            'processing_time_ms': processing_time,
            'total_results': len(result.businesses),
            'filters_applied': result.filters_applied,
            'radius_expanded': result.radius_expanded,
            'cached': False
        })
    
    def get_processing_time(self, search_id: str) -> float:
        """Get processing time for a search ID."""
        start_time = self._start_times.get(search_id)
        if start_time is None:
            return 0.0
        
        end_time = time.time()
        return round((end_time - start_time) * 1000, 2)  # ms


class SearchResponseBuilder(IResponseBuilder):
    """
    Response building service.
    
    Single Responsibility: Build API responses only.
    """
    
    def __init__(self, metrics_service: IMetricsService, logger: ILogger):
        self.metrics_service = metrics_service
        self.logger = logger
    
    def build_success_response(self, result: SearchResult, search_id: str, 
                             cached: bool = False, cache_key: str = None) -> Dict[str, Any]:
        """Build successful search response with metadata."""
        # Build search locations summary
        search_locations_summary = []
        for loc in result.locations:
            if "state" in loc:
                search_locations_summary.append({
                    "type": "state",
                    "state": loc["state"]
                })
            elif "lat" in loc and "lng" in loc:
                search_locations_summary.append({
                    "type": "geo",
                    "lat": float(loc["lat"]),
                    "lng": float(loc["lng"])
                })
        
        # Calculate performance metrics
        processing_time = self.metrics_service.get_processing_time(search_id)
        
        # Build search metadata
        search_metadata = {
            "total_count": len(result.businesses),
            "total_found": min(result.total_found, 100),  # Cap at 100 for now
            "radius_used": float(result.radius_used),
            "radius_expanded": result.radius_expanded,
            "filters_applied": result.filters_applied,
            "search_locations": search_locations_summary,
            "performance": {
                "processing_time_ms": processing_time,
                "search_id": search_id,
                "cached": cached
            }
        }
        
        # Add radius-specific metadata if geo search was performed
        if result.geo_locations:
            search_metadata["radius_requested"] = float(result.radius_miles)
            if result.radii_tried:
                search_metadata["radius_expansion_sequence"] = result.radii_tried
        
        # Add cache key if cached
        if cached and cache_key:
            search_metadata["cache_key"] = cache_key
        
        return {
            "results": BusinessSerializer(result.businesses, many=True).data,
            "search_metadata": search_metadata
        }
    
    def build_validation_error_response(self, errors: Dict[str, Any], 
                                      search_id: str) -> Response:
        """Build validation error response."""
        self.logger.warning(f"[{search_id}] Invalid input", extra={
            'search_id': search_id,
            'validation_errors': errors
        })
        
        return Response(
            {"error": "Invalid input", "details": errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def build_server_error_response(self, error: Exception, 
                                  search_id: str) -> Response:
        """Build server error response."""
        # Don't catch DRF validation/parsing errors - let them bubble up
        from rest_framework.exceptions import ValidationError, ParseError
        
        if isinstance(error, (ValidationError, ParseError)):
            raise  # Let DRF handle these
        
        processing_time = self.metrics_service.get_processing_time(search_id)
        
        self.logger.error(f"[{search_id}] Search failed", extra={
            'search_id': search_id,
            'processing_time_ms': processing_time,
            'error': str(error),
            'error_type': type(error).__name__
        }, exc_info=True)
        
        return Response({
            "error": "Internal server error",
            "search_id": search_id,
            "message": "An error occurred while processing your search. Please try again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DjangoLogger(ILogger):
    """
    Django logging implementation.
    
    Single Responsibility: Handle logging operations only.
    """
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log info message."""
        self.logger.info(message, extra=extra or {})
    
    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=extra or {})
    
    def error(self, message: str, extra: Dict[str, Any] = None, 
              exc_info: bool = False) -> None:
        """Log error message."""
        self.logger.error(message, extra=extra or {}, exc_info=exc_info)
