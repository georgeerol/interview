import time
import logging
from typing import Dict, Any, List

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from .models import Business
from .serializers import BusinessSerializer, BusinessSearchRequestSerializer
from .utils import get_businesses_within_radius, expand_radius_search_multiple_locations

# Configure logging
logger = logging.getLogger(__name__)


class BusinessViewSet(viewsets.ModelViewSet):
	queryset = Business.objects.all().order_by("name")
	serializer_class = BusinessSerializer
	permission_classes = [AllowAny]

	@action(detail=False, methods=["post"], url_path="search")
	def search(self, request):
		"""
		Search businesses by location filters (states and/or lat/lng + radius) and optional text.
		
		Production-optimized with caching, performance monitoring, and error handling.
		
		Expected input:
		{
			"locations": [
				{"state": "CA"},
				{"lat": 34.052235, "lng": -118.243683}
			],
			"radius_miles": 50,
			"text": "coffee"
		}
		"""
		# Phase 8: Performance monitoring
		start_time = time.time()
		search_id = f"search_{int(start_time * 1000)}"
		
		try:
			logger.info(f"[{search_id}] Business search started", extra={
				'search_id': search_id,
				'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
			})
			
			# Phase 1: Validate input
			serializer = BusinessSearchRequestSerializer(data=request.data)
			if not serializer.is_valid():
				logger.warning(f"[{search_id}] Invalid input", extra={
					'search_id': search_id,
					'validation_errors': serializer.errors
				})
				return Response(
					{"error": "Invalid input", "details": serializer.errors},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Phase 8: Check cache for frequent searches
			cache_key = self._generate_cache_key(request.data)
			cached_result = cache.get(cache_key)
			if cached_result:
				logger.info(f"[{search_id}] Cache hit", extra={
					'search_id': search_id,
					'cache_key': cache_key
				})
				# Update cache metadata
				cached_result['search_metadata']['performance']['cached'] = True
				cached_result['search_metadata']['performance']['search_id'] = search_id
				cached_result['search_metadata']['cache_key'] = cache_key
				return Response(cached_result, status=status.HTTP_200_OK)
			
			# Continue with search logic
			validated_data = serializer.validated_data
			locations = validated_data.get("locations", [])
			text = validated_data.get("text", "")
			radius_miles = validated_data.get("radius_miles")
			
			# Phase 3: Basic search logic - start with all businesses
			businesses = Business.objects.all()
			filters_applied = []
			
			# Apply text filtering if provided
			if text:
				businesses = businesses.filter(name__icontains=text)
				filters_applied.append("text")
			
			# Apply state filtering
			state_locations = [loc for loc in locations if "state" in loc]
			geo_locations = [loc for loc in locations if "lat" in loc and "lng" in loc]
			
			if state_locations:
				# Filter by states using OR logic
				state_codes = [loc["state"] for loc in state_locations]
				businesses = businesses.filter(state__in=state_codes)
				filters_applied.append("state")
			
			# Phase 4 & 5: Handle geo-location filtering with radius expansion
			final_businesses = []
			radius_used = radius_miles if radius_miles is not None else 50.0  # Default for state-only searches
			radius_expanded = False
			radii_tried = []
			
			if geo_locations:
				filters_applied.append("geo")
				
				# Start with all businesses for geo filtering (apply text filter if needed)
				base_businesses = Business.objects.all()
				if text:
					base_businesses = base_businesses.filter(name__icontains=text)
				
				# Phase 5: Use radius expansion for geo locations
				geo_businesses, radius_used, radius_expanded, radii_tried = expand_radius_search_multiple_locations(
					base_businesses, 
					geo_locations, 
					radius_miles
				)
				
				# Combine state-filtered and geo-filtered results (OR logic)
				if state_locations:
					# Add state-filtered businesses to geo results
					state_businesses = list(businesses)  # Already filtered by state and text
					final_businesses = geo_businesses + state_businesses
				else:
					# Only geo filtering
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
				business_list = list(businesses[:100])  # Limit to 100 for now
		
			# Phase 6: Build comprehensive search metadata
			total_found = len(final_businesses) if geo_locations else len(list(businesses))
			
			# Build search locations summary
			search_locations_summary = []
			for loc in locations:
				if "state" in loc:
					search_locations_summary.append({
						"type": "state",
						"state": loc["state"]
					})
				elif "lat" in loc and "lng" in loc:
					search_locations_summary.append({
						"type": "geo",
						"lat": float(loc["lat"]),
						"lng": float(loc["lng"])
					})
			
			# Build metadata with performance metrics
			end_time = time.time()
			processing_time = round((end_time - start_time) * 1000, 2)  # ms
			
			search_metadata = {
				"total_count": len(business_list),
				"total_found": min(total_found, 100),  # Cap at 100 for now
				"radius_used": float(radius_used),
				"radius_expanded": radius_expanded,
				"filters_applied": filters_applied,
				"search_locations": search_locations_summary,
				"performance": {
					"processing_time_ms": processing_time,
					"search_id": search_id,
					"cached": False
				}
			}
			
			# Add radius-specific metadata if geo search was performed
			if geo_locations:
				search_metadata["radius_requested"] = float(radius_miles)
				if radii_tried:
					search_metadata["radius_expansion_sequence"] = radii_tried
			
			# Phase 8: Cache the result for frequent searches
			result_data = {
				"results": BusinessSerializer(business_list, many=True).data,
				"search_metadata": search_metadata
			}
			
			# Cache for 5 minutes for frequently accessed searches
			cache_timeout = getattr(settings, 'BUSINESS_SEARCH_CACHE_TIMEOUT', 300)
			cache.set(cache_key, result_data, cache_timeout)
			
			# Log successful search
			logger.info(f"[{search_id}] Search completed successfully", extra={
				'search_id': search_id,
				'processing_time_ms': processing_time,
				'total_results': len(business_list),
				'filters_applied': filters_applied,
				'radius_expanded': radius_expanded,
				'cached': False
			})
			
			return Response(result_data, status=status.HTTP_200_OK)
			
		except Exception as e:
			# Phase 8: Production error handling for unexpected errors only
			# Don't catch DRF validation/parsing errors - let them bubble up
			from rest_framework.exceptions import ValidationError, ParseError
			
			if isinstance(e, (ValidationError, ParseError)):
				raise  # Let DRF handle these
			
			end_time = time.time()
			processing_time = round((end_time - start_time) * 1000, 2)
			
			logger.error(f"[{search_id}] Search failed", extra={
				'search_id': search_id,
				'processing_time_ms': processing_time,
				'error': str(e),
				'error_type': type(e).__name__
			}, exc_info=True)
			
			return Response({
				"error": "Internal server error",
				"search_id": search_id,
				"message": "An error occurred while processing your search. Please try again."
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	
	def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
		"""Generate a cache key for the search request"""
		import hashlib
		import json
		
		# Create a normalized version of the request for consistent caching
		normalized_data = {
			'locations': sorted(request_data.get('locations', []), key=str),
			'radius_miles': request_data.get('radius_miles'),
			'text': request_data.get('text', '').strip().lower()
		}
		
		# Create hash of the normalized request
		data_str = json.dumps(normalized_data, sort_keys=True)
		cache_key = f"business_search:{hashlib.md5(data_str.encode()).hexdigest()}"
		return cache_key


