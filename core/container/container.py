"""
Dependency Injection Container

Service container that manages and provides access to all application services
with proper dependency resolution and lifecycle management.
"""
from typing import Dict, Any

from ..search import BusinessSearchService, BusinessSearchServiceImpl
from ..cache import CacheService, DjangoCacheService
from ..metrics import MetricsService, SearchMetricsService
from ..response import ResponseBuilder, SearchResponseBuilder
from ..logging import Logger, DjangoLogger


class ServiceContainer:
    """
    Service container for dependency injection and service management.
    
    Manages the creation and lifecycle of all application services,
    handling dependency resolution and providing access through properties.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """
        Initialize all application services with dependency resolution.
        
        Creates services in dependency order: logger first, then services
        that depend on it, ensuring proper initialization sequence.
        """
        # Create logger first (no dependencies)
        logger = DjangoLogger()
        self._services['logger'] = logger
        
        # Create cache service (no dependencies)
        cache_service = DjangoCacheService()
        self._services['cache_service'] = cache_service
        
        # Create metrics service (depends on logger)
        metrics_service = SearchMetricsService(logger)
        self._services['metrics_service'] = metrics_service
        
        # Create search service (no dependencies - pure business logic)
        search_service = BusinessSearchServiceImpl()
        self._services['search_service'] = search_service
        
        # Create response builder (depends on metrics and logger)
        response_builder = SearchResponseBuilder(metrics_service, logger)
        self._services['response_builder'] = response_builder
    
    @property
    def search_service(self) -> BusinessSearchService:
        """
        Get the business search service instance.
        
        Returns:
            BusinessSearchService: Core search logic implementation
        """
        return self._services['search_service']
    
    @property
    def cache_service(self) -> CacheService:
        """
        Get the cache service instance.
        
        Returns:
            CacheService: Caching operations for performance optimization
        """
        return self._services['cache_service']
    
    @property
    def metrics_service(self) -> MetricsService:
        """
        Get the metrics service instance.
        
        Returns:
            MetricsService: Performance tracking and monitoring
        """
        return self._services['metrics_service']
    
    @property
    def response_builder(self) -> ResponseBuilder:
        """
        Get the response builder service instance.
        
        Returns:
            ResponseBuilder: Structured API response construction
        """
        return self._services['response_builder']
    
    @property
    def logger(self) -> Logger:
        """
        Get the logger service instance.
        
        Returns:
            Logger: Centralized logging for debugging and monitoring
        """
        return self._services['logger']


# Global container instance (singleton pattern)
_container = None


def get_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Uses singleton pattern to ensure only one container instance exists
    throughout the application lifecycle.
    
    Returns:
        ServiceContainer: The global service container instance
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container