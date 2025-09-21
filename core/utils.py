"""
Utility functions for business search functionality
"""
import math
from decimal import Decimal
from typing import Union, List, Tuple

from .constants import RADIUS_EXPANSION_SEQUENCE


def haversine_distance(lat1: Union[float, Decimal], lon1: Union[float, Decimal], 
                      lat2: Union[float, Decimal], lon2: Union[float, Decimal]) -> float:
    """
    Calculate the great circle distance in miles between two points 
    on the earth (specified in decimal degrees) using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        Distance in miles
        
    Formula:
        a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
        c = 2 ⋅ atan2( √a, √(1−a) )
        d = R ⋅ c
        
    Where:
        φ is latitude, λ is longitude, R is earth's radius (3959 miles)
        Δφ is the difference in latitude, Δλ is the difference in longitude
    """
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
    """
    Check if a business is within a given radius of a search point.
    
    Args:
        business_lat, business_lon: Business coordinates
        search_lat, search_lon: Search point coordinates  
        radius_miles: Search radius in miles
        
    Returns:
        True if business is within radius, False otherwise
    """
    distance = haversine_distance(business_lat, business_lon, search_lat, search_lon)
    return distance <= float(radius_miles)


def get_businesses_within_radius(businesses, search_lat: Union[float, Decimal], 
                               search_lon: Union[float, Decimal], 
                               radius_miles: Union[float, Decimal]):
    """
    Filter businesses to only those within the specified radius of a search point.
    
    Args:
        businesses: QuerySet or iterable of Business objects
        search_lat, search_lon: Search point coordinates
        radius_miles: Search radius in miles
        
    Returns:
        List of businesses within radius, with distance attribute added
    """
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
    """
    Validate that coordinates are within valid ranges.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        lat, lon = float(lat), float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def expand_radius_search(businesses, search_lat: Union[float, Decimal], 
                        search_lng: Union[float, Decimal], 
                        initial_radius: Union[float, Decimal]) -> Tuple[List, float, bool, List[float]]:
    """
    Perform radius expansion search according to the sequence [1, 5, 10, 25, 50, 100, 500].
    
    If no results are found within the initial radius, expand incrementally through the 
    sequence until matches are found or max radius (500) is reached.
    
    Args:
        businesses: QuerySet or iterable of Business objects to search
        search_lat, search_lng: Search point coordinates
        initial_radius: Initial radius to try first
        
    Returns:
        Tuple of (matching_businesses, actual_radius_used, was_expanded, radii_tried)
    """
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
    """
    Perform radius expansion search for multiple geo locations.
    
    Tries initial radius for all locations first. If no results found anywhere,
    expands radius incrementally until matches are found or max radius reached.
    
    Args:
        businesses: QuerySet or iterable of Business objects to search
        geo_locations: List of {"lat": X, "lng": Y} dictionaries
        initial_radius: Initial radius to try first
        
    Returns:
        Tuple of (matching_businesses, actual_radius_used, was_expanded, radii_tried)
    """
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
