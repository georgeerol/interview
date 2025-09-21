"""
Response Builder Implementation

Service for constructing structured API responses with comprehensive
metadata for business search operations.
"""

from typing import Dict, Any
from rest_framework import status
from rest_framework.response import Response

from .interface import ResponseBuilder
from ..search import SearchResult
from ..metrics import MetricsService
from ..logging import Logger
from ..api.serializers import BusinessSerializer


class SearchResponseBuilder(ResponseBuilder):
    """
    Response builder service for business search API responses.
    
    Constructs structured responses with comprehensive metadata including
    performance metrics, search transparency, and error handling.
    """
    
    def __init__(self, metrics_service: MetricsService, logger: Logger):
        """
        Initialize response builder with required services.
        
        Args:
            metrics_service: Service for performance metrics calculation
            logger: Logger for error and validation logging
        """
        self.metrics_service = metrics_service
        self.logger = logger
    
    def build_success_response(self, result: SearchResult, search_id: str, 
                             cached: bool = False, cache_key: str = None) -> Dict[str, Any]:
        """
        Build successful search response with comprehensive metadata.
        
        Constructs a structured response containing search results and detailed
        metadata including performance metrics, search transparency, and caching info.
        
        Args:
            result: Search result object containing businesses and operation details
            search_id: Unique search identifier for tracking
            cached: Whether the response was served from cache
            cache_key: Cache key used if response was cached
            
        Returns:
            Dictionary containing 'results' and 'search_metadata' keys
        """
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
        """
        Build validation error response for invalid input.
        
        Args:
            errors: Validation error details from serializer
            search_id: Unique search identifier for tracking
            
        Returns:
            HTTP 400 Response with error details
        """
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
        """
        Build server error response for unexpected exceptions.
        
        Handles internal server errors while preserving DRF validation
        and parsing errors. Logs error details for debugging.
        
        Args:
            error: Exception that occurred during processing
            search_id: Unique search identifier for tracking
            
        Returns:
            HTTP 500 Response with error message and search ID
        """
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
