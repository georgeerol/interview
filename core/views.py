from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Business
from .serializers import BusinessSerializer, BusinessSearchRequestSerializer


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
		
		# TODO: Phases 2-6: Implement search logic
		# For now, return empty results with the validated input structure
		return Response({
			"results": [],
			"search_metadata": {
				"input_received": validated_data,
				"total_count": 0,
				"radius_used": validated_data.get("radius_miles"),
				"radius_expanded": False,
				"filters_applied": []
			}
		}, status=status.HTTP_200_OK)


