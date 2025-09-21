"""
Logging Package

Everything related to logging functionality.
Contains interfaces and implementations for logging operations.
"""

from .interface import Logger
from .service import DjangoLogger

__all__ = [
    "Logger",
    "DjangoLogger",
]
