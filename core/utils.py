"""Business search utility functions.

Geospatial calculations and radius expansion logic for the business search API.
"""
import math
from decimal import Decimal
from typing import Union, List, Tuple

from .constants import RADIUS_EXPANSION_SEQUENCE


def haversine_distance(lat1: Union[float, Decimal], lon1: Union[float, Decimal], 
                      lat2: Union[float, Decimal], lon2: Union[float, Decimal]) -> float:
    """Calculate great circle distance in miles between two points using Haversine formula."""

    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    earth_radius_miles = 3959
    distance = earth_radius_miles * c
    
    return distance


def is_within_radius(business_lat: Union[float, Decimal], business_lon: Union[float, Decimal],
                    search_lat: Union[float, Decimal], search_lon: Union[float, Decimal],
                    radius_miles: Union[float, Decimal]) -> bool:
    """Check if a business is within given radius of a search point."""
    distance = haversine_distance(business_lat, business_lon, search_lat, search_lon)
    return distance <= float(radius_miles)


def get_businesses_within_radius(businesses, search_lat: Union[float, Decimal], 
                               search_lon: Union[float, Decimal], 
                               radius_miles: Union[float, Decimal]):
    """Filter businesses within specified radius and add distance attribute."""
    businesses_in_radius = []
    
    for business in businesses:
        distance = haversine_distance(
            business.latitude, business.longitude, 
            search_lat, search_lon
        )
        
        if distance <= float(radius_miles):
            # Add distance as an attribute for potential sorting/display
            business.distance = distance
            businesses_in_radius.append(business)
    
    return businesses_in_radius


def validate_coordinates(lat: Union[float, Decimal], lon: Union[float, Decimal]) -> bool:
    """Validate coordinates are within valid ranges (-90/90 lat, -180/180 lng)."""
    try:
        lat, lon = float(lat), float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def expand_radius_search(businesses, search_lat: Union[float, Decimal], 
                        search_lng: Union[float, Decimal], 
                        initial_radius: Union[float, Decimal]) -> Tuple[List, float, bool, List[float]]:
    """Expand search radius through [1,5,10,25,50,100,500] sequence until results found."""
    initial_radius = float(initial_radius)
    radii_tried = [initial_radius]
    
    # First try the requested radius
    results = get_businesses_within_radius(businesses, search_lat, search_lng, initial_radius)
    if results:
        return results, initial_radius, False, radii_tried
    
    # If no results, try expansion sequence
    for radius in RADIUS_EXPANSION_SEQUENCE:
        if radius <= initial_radius:
            continue  # Skip radii smaller than or equal to what we already tried
            
        radii_tried.append(float(radius))
        results = get_businesses_within_radius(businesses, search_lat, search_lng, radius)
        if results:
            return results, float(radius), True, radii_tried
    
    # No results found even at max radius
    return [], 500.0, True, radii_tried


def expand_radius_search_multiple_locations(businesses, geo_locations: List[dict], 
                                          initial_radius: Union[float, Decimal]) -> Tuple[List, float, bool, List[float]]:
    """Expand radius search across multiple geo locations with deduplication."""
    initial_radius = float(initial_radius)
    radii_tried = [initial_radius]
    
    # First try the requested radius for all locations
    all_results = []
    for geo_location in geo_locations:
        search_lat = geo_location["lat"]
        search_lng = geo_location["lng"]
        
        location_results = get_businesses_within_radius(
            businesses, search_lat, search_lng, initial_radius
        )
        all_results.extend(location_results)
    
    # Remove duplicates
    if all_results:
        seen_ids = set()
        unique_results = []
        for business in all_results:
            if business.id not in seen_ids:
                seen_ids.add(business.id)
                unique_results.append(business)
        return unique_results, initial_radius, False, radii_tried
    
    # If no results, try expansion sequence
    for radius in RADIUS_EXPANSION_SEQUENCE:
        if radius <= initial_radius:
            continue  # Skip radii smaller than or equal to what we already tried
            
        radii_tried.append(float(radius))
        all_results = []
        for geo_location in geo_locations:
            search_lat = geo_location["lat"]
            search_lng = geo_location["lng"]
            
            location_results = get_businesses_within_radius(
                businesses, search_lat, search_lng, radius
            )
            all_results.extend(location_results)
        
        # Remove duplicates
        if all_results:
            seen_ids = set()
            unique_results = []
            for business in all_results:
                if business.id not in seen_ids:
                    seen_ids.add(business.id)
                    unique_results.append(business)
            return unique_results, float(radius), True, radii_tried
    
    # No results found even at max radius
    return [], 500.0, True, radii_tried
