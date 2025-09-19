from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import Business
from .serializers import BusinessSerializer, BusinessSearchRequestSerializer
from .utils import get_businesses_within_radius, expand_radius_search_multiple_locations


class BusinessViewSet(viewsets.ModelViewSet):
	queryset = Business.objects.all().order_by("name")
	serializer_class = BusinessSerializer
	permission_classes = [AllowAny]

	@action(detail=False, methods=["post"], url_path="search")
	def search(self, request):
		"""
		Search businesses by location filters (states and/or lat/lng + radius) and optional text.
		
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
		# Phase 1: Validate input
		serializer = BusinessSearchRequestSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(
				{"error": "Invalid input", "details": serializer.errors}, 
				status=status.HTTP_400_BAD_REQUEST
			)
		
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
		
		# Build metadata
		search_metadata = {
			"total_count": len(business_list),
			"total_found": min(total_found, 100),  # Cap at 100 for now
			"radius_used": float(radius_used),
			"radius_expanded": radius_expanded,
			"filters_applied": filters_applied,
			"search_locations": search_locations_summary
		}
		
		# Add radius-specific metadata if geo search was performed
		if geo_locations:
			search_metadata["radius_requested"] = float(radius_miles)
			if radii_tried:
				search_metadata["radius_expansion_sequence"] = radii_tried
		
		return Response({
			"results": BusinessSerializer(business_list, many=True).data,
			"search_metadata": search_metadata
		}, status=status.HTTP_200_OK)


