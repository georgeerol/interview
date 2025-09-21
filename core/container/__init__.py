"""
Core Container Package

Dependency injection container for managing service lifecycles.
Implements the Service Locator pattern with SOLID principles.
"""

from .container import ServiceContainer, get_container

__all__ = [
    "ServiceContainer",
    "get_container",
]
