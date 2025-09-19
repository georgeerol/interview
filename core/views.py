from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import Business
from .serializers import BusinessSerializer, BusinessSearchRequestSerializer
from .utils import get_businesses_within_radius


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
		
		# Phase 4 will handle geo locations, for now just note if they exist
		if geo_locations:
			filters_applied.append("geo")  # Will be implemented in Phase 4
		
		# For Phase 3, we only handle state and text filtering
		# Geo filtering will be added in Phase 4
		if geo_locations and not state_locations:
			# If only geo locations provided, we'll need Phase 4 logic
			# For now, return empty results with a note
			businesses = Business.objects.none()
		
		# Get results and prepare response
		business_list = list(businesses[:100])  # Limit to 100 for now
		
		return Response({
			"results": BusinessSerializer(business_list, many=True).data,
			"search_metadata": {
				"total_count": len(business_list),
				"radius_used": radius_miles,
				"radius_expanded": False,
				"filters_applied": filters_applied,
				"note": "Geo-location filtering will be implemented in Phase 4" if geo_locations else None
			}
		}, status=status.HTTP_200_OK)


