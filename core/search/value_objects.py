"""
Search Value Objects

Immutable data structures for encapsulating search parameters and results
in business search operations.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from ..domain import Business


@dataclass
class SearchParams:
    """
    Immutable data structure for search parameters.
    
    Attributes:
        locations: List of location filters (state or lat/lng objects)
        radius_miles: Optional radius in miles for geospatial searches
        text: Optional text filter for business name search
    """
    locations: List[Dict[str, Any]]
    radius_miles: Optional[float] = None
    text: str = ""


@dataclass 
class SearchResult:
    """
    Immutable data structure for search operation results.
    
    Contains the search results along with comprehensive metadata about
    the search operation including performance and transparency details.
    
    Attributes:
        businesses: List of Business objects matching the search criteria
        total_found: Total number of businesses found before pagination
        filters_applied: List of filter types used ("text", "state", "geo")
        locations: Original location parameters from the search request
        geo_locations: Subset of locations that were geospatial searches
        radius_used: Final radius used in miles (after any expansion)
        radius_expanded: Whether radius expansion was performed
        radii_tried: List of radii attempted during expansion
        radius_miles: Originally requested radius in miles
    """
    businesses: List[Business]
    total_found: int
    filters_applied: List[str]
    locations: List[Dict[str, Any]]
    geo_locations: List[Dict[str, Any]]
    radius_used: float
    radius_expanded: bool
    radii_tried: List[float]
    radius_miles: Optional[float]
