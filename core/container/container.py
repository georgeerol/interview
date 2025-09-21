"""
Dependency Injection Container

Manages all dependencies and their lifecycles following SOLID principles.
Implements Dependency Inversion Principle by providing abstractions to consumers.
"""
from typing import Dict, Any
from django.conf import settings

from ..interfaces import (
    BusinessSearchService as BusinessSearchServiceInterface,
    CacheService as CacheServiceInterface, 
    MetricsService as MetricsServiceInterface,
    ResponseBuilder as ResponseBuilderInterface, 
    Logger as LoggerInterface
)
from ..services import (
    BusinessSearchService, DjangoCacheService, SearchMetricsService,
    SearchResponseBuilder, DjangoLogger
)


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
        search_service = BusinessSearchService()
        self._services['search_service'] = search_service
        
        # Create response builder (depends on metrics and logger)
        response_builder = SearchResponseBuilder(metrics_service, logger)
        self._services['response_builder'] = response_builder
    
    @property
    def search_service(self) -> BusinessSearchServiceInterface:
        """Get business search service."""
        return self._services['search_service']
    
    @property
    def cache_service(self) -> CacheServiceInterface:
        """Get cache service."""
        return self._services['cache_service']
    
    @property
    def metrics_service(self) -> MetricsServiceInterface:
        """Get metrics service."""
        return self._services['metrics_service']
    
    @property
    def response_builder(self) -> ResponseBuilderInterface:
        """Get response builder service."""
        return self._services['response_builder']
    
    @property
    def logger(self) -> LoggerInterface:
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
