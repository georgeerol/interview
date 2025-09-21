
"""
Metrics Service Implementation

Performance monitoring service for tracking business search operations
with timing measurements and structured logging.
"""
import time
from typing import Dict

from .interface import MetricsService
from ..search import SearchResult
from ..logging import Logger


class SearchMetricsService(MetricsService):
    """
    Performance monitoring service implementation for business search operations.
    
    Tracks search request timing, logs performance metrics, and provides
    structured monitoring data for debugging and optimization.
    """
    
    def __init__(self, logger: Logger):
        """
        Initialize metrics service with logger dependency.
        
        Args:
            logger: Logger instance for structured logging
        """
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    def start_tracking(self, request) -> str:
        """
        Start performance tracking for a search request.
        
        Creates a unique search ID based on timestamp and logs the start
        of the search operation with request metadata.
        
        Args:
            request: HTTP request object to track
            
        Returns:
            Unique search ID string for tracking this request
        """
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
        """
        Log successful completion of a search operation.
        
        Records performance metrics and search result details for
        monitoring and debugging purposes.
        
        Args:
            search_id: Unique search ID from start_tracking
            result: Search result object containing operation details
        """
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
        """
        Get processing time for a completed search operation.
        
        Calculates the elapsed time from start_tracking to now,
        returning the result in milliseconds.
        
        Args:
            search_id: Unique search ID from start_tracking
            
        Returns:
            Processing time in milliseconds, or 0.0 if search ID not found
        """
        start_time = self._start_times.get(search_id)
        if start_time is None:
            return 0.0
        
        end_time = time.time()
        return round((end_time - start_time) * 1000, 2)  # ms
