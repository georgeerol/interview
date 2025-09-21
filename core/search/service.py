"""
Business Search Service Implementation

Concrete implementation of business search operations following SOLID principles.
"""
from .interface import BusinessSearchService
from .value_objects import SearchParams, SearchResult
from ..domain import Business
from ..infrastructure import expand_radius_search_multiple_locations


class BusinessSearchServiceImpl(BusinessSearchService):
    """
    Core business search service implementation.
    
    Single Responsibility: Handle business search logic only.
    No dependencies on HTTP, caching, or logging concerns.
    """
    
    def search(self, params: SearchParams) -> SearchResult:
        """Perform business search based on provided parameters."""
        # Initialize search state
        businesses = Business.objects.all()
        filters_applied = []
        
        # Apply text filtering if provided
        if params.text:
            businesses = businesses.filter(name__icontains=params.text)
            filters_applied.append("text")
        
        # Separate location types
        state_locations = [loc for loc in params.locations if "state" in loc]
        geo_locations = [loc for loc in params.locations if "lat" in loc and "lng" in loc]
        
        # Apply state filtering
        if state_locations:
            state_codes = [loc["state"] for loc in state_locations]
            businesses = businesses.filter(state__in=state_codes)
            filters_applied.append("state")
        
        # Handle geo-location filtering with radius expansion
        final_businesses = []
        radius_used = params.radius_miles if params.radius_miles is not None else 50.0
        radius_expanded = False
        radii_tried = []
        
        if geo_locations:
            filters_applied.append("geo")
            
            # Start with all businesses for geo filtering
            base_businesses = Business.objects.all()
            if params.text:
                base_businesses = base_businesses.filter(name__icontains=params.text)
            
            # Apply radius expansion for geo locations
            geo_businesses, radius_used, radius_expanded, radii_tried = expand_radius_search_multiple_locations(
                base_businesses, 
                geo_locations, 
                params.radius_miles
            )
            
            # Combine state-filtered and geo-filtered results (OR logic)
            if state_locations:
                state_businesses = list(businesses)  # Already filtered by state and text
                final_businesses = geo_businesses + state_businesses
            else:
                final_businesses = geo_businesses
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_businesses = []
            for business in final_businesses:
                if business.id not in seen_ids:
                    seen_ids.add(business.id)
                    unique_businesses.append(business)
            
            business_list = unique_businesses[:100]  # Limit to 100
        else:
            # No geo locations, use existing state/text filtered results
            business_list = list(businesses[:100])
        
        # Calculate total found for metadata
        total_found = len(final_businesses) if geo_locations else len(list(businesses))
        
        return SearchResult(
            businesses=business_list,
            total_found=total_found,
            filters_applied=filters_applied,
            locations=params.locations,
            geo_locations=geo_locations,
            radius_used=radius_used,
            radius_expanded=radius_expanded,
            radii_tried=radii_tried,
            radius_miles=params.radius_miles
        )
