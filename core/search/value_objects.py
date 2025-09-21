"""
Search Value Objects

Data transfer objects for search operations following Domain-Driven Design principles.
These are immutable data structures that encapsulate search parameters and results.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from ..domain import Business


@dataclass
class SearchParams:
    """Value object for search parameters."""
    locations: List[Dict[str, Any]]
    radius_miles: Optional[float] = None
    text: str = ""


@dataclass 
class SearchResult:
    """Value object for search results."""
    businesses: List[Business]
    total_found: int
    filters_applied: List[str]
    locations: List[Dict[str, Any]]
    geo_locations: List[Dict[str, Any]]
    radius_used: float
    radius_expanded: bool
    radii_tried: List[float]
    radius_miles: Optional[float]
