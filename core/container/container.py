"""
Dependency Injection Container

Manages all dependencies and their lifecycles following SOLID principles.
Implements Dependency Inversion Principle by providing abstractions to consumers.
"""
from typing import Dict, Any

from ..search import BusinessSearchService, BusinessSearchServiceImpl
from ..cache import CacheService, DjangoCacheService
from ..metrics import MetricsService, SearchMetricsService
from ..response import ResponseBuilder, SearchResponseBuilder
from ..logging import Logger, DjangoLogger


class ServiceContainer:
    """
    Dependency injection container following SOLID principles.
    
    - Single Responsibility: Manage service dependencies
    - Open/Closed: Easy to add new services without modification
    - Dependency Inversion: Provides abstractions, not concretions
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize all services with proper dependency injection."""
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
        """Get business search service."""
        return self._services['search_service']
    
    @property
    def cache_service(self) -> CacheService:
        """Get cache service."""
        return self._services['cache_service']
    
    @property
    def metrics_service(self) -> MetricsService:
        """Get metrics service."""
        return self._services['metrics_service']
    
    @property
    def response_builder(self) -> ResponseBuilder:
        """Get response builder service."""
        return self._services['response_builder']
    
    @property
    def logger(self) -> Logger:
        """Get logger service."""
        return self._services['logger']


# Global container instance (singleton pattern)
_container = None


def get_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Implements singleton pattern for dependency management.
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container