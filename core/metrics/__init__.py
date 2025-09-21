"""
Metrics Package

Everything related to performance monitoring and metrics.
Contains interfaces and implementations for tracking search performance.
"""

from .interface import MetricsService
from .service import SearchMetricsService

__all__ = [
    "MetricsService",
    "SearchMetricsService",
]
