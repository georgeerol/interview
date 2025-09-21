"""
Metrics Service Implementation

Performance monitoring service following SOLID principles.
"""
import time
from typing import Dict

from .interface import MetricsService
from ..search import SearchResult
from ..logging import Logger


class SearchMetricsService(MetricsService):
    """
    Performance monitoring service.
    
    Single Responsibility: Handle performance tracking only.
    """
    
    def __init__(self, logger: Logger):
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
