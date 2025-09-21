"""Business Search API Serializers.

Validate search requests and format responses for the business search endpoint.
"""
from rest_framework import serializers
from typing import Dict, Any, List
from decimal import Decimal

from ..domain import Business
from ..infrastructure import US_STATES


class LocationSerializer(serializers.Serializer):
	"""Validate location filters - either state OR lat/lng coordinates, not both."""
	state = serializers.CharField(max_length=2, required=False)
	lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
	lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
	
	def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Ensure location has either state OR lat/lng, validate bounds and state codes."""
		has_state = 'state' in data and data['state'] is not None
		has_coords = ('lat' in data and data['lat'] is not None and 
					  'lng' in data and data['lng'] is not None)
		
		if has_state and has_coords:
			raise serializers.ValidationError(
				"Location cannot have both state and lat/lng coordinates"
			)
		
		if not has_state and not has_coords:
			raise serializers.ValidationError(
				"Location must have either state or lat/lng coordinates"
			)
		
		# Validate state code if provided
		if has_state:
			valid_states = [code for code, name in US_STATES]
			if data['state'].upper() not in valid_states:
				raise serializers.ValidationError(
					f"Invalid state code: {data['state']}. Must be a valid US state."
				)
			data['state'] = data['state'].upper()
		
		# Validate coordinates if provided
		if has_coords:
			lat, lng = data['lat'], data['lng']
			if not (-90 <= lat <= 90):
				raise serializers.ValidationError(
					f"Latitude must be between -90 and 90, got {lat}"
				)
			if not (-180 <= lng <= 180):
				raise serializers.ValidationError(
					f"Longitude must be between -180 and 180, got {lng}"
				)
		
		return data


class BusinessSearchRequestSerializer(serializers.Serializer):
	"""Validate business search requests. Auto-sets 50mi radius for geo searches."""
	locations = LocationSerializer(many=True, required=True)
	radius_miles = serializers.DecimalField(
		max_digits=6, 
		decimal_places=2, 
		min_value=Decimal('0.1'), 
		max_value=Decimal('1000'),
		required=False,
		help_text="Radius in miles for lat/lng searches"
	)
	text = serializers.CharField(
		max_length=255, 
		required=False, 
		allow_blank=True,
		help_text="Text to search in business names (case-insensitive)"
	)
	
	def validate_locations(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Ensure 1-20 locations provided."""
		if not locations:
			raise serializers.ValidationError("At least one location filter is required")
		
		if len(locations) > 20:  # Reasonable limit
			raise serializers.ValidationError("Too many location filters (max 20)")
		
		return locations
	
	def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Set default 50mi radius for geo searches if not provided."""
		locations = data.get('locations', [])
		radius_miles = data.get('radius_miles')
		
		# Check if any location has lat/lng coordinates
		has_geo_locations = any(
			'lat' in loc and 'lng' in loc 
			for loc in locations
		)
		
		# If there are geo locations but no radius specified, set default
		if has_geo_locations and radius_miles is None:
			data['radius_miles'] = 50  # Default radius of 50 miles
		
		return data


class BusinessSerializer(serializers.ModelSerializer):
	"""Serialize Business model objects."""
	class Meta:
		model = Business
		fields = [
			"id",
			"name",
			"city",
			"state",
			"latitude",
			"longitude",
		]


class SearchMetadataSerializer(serializers.Serializer):
	"""Search result metadata including radius expansion and performance info."""
	total_count = serializers.IntegerField(help_text="Number of businesses returned")
	total_found = serializers.IntegerField(help_text="Total businesses found before pagination")
	radius_requested = serializers.DecimalField(
		max_digits=6, decimal_places=2, required=False,
		help_text="Originally requested radius in miles"
	)
	radius_used = serializers.DecimalField(
		max_digits=6, decimal_places=2,
		help_text="Actual radius used in miles"
	)
	radius_expanded = serializers.BooleanField(
		help_text="Whether radius was expanded from original request"
	)
	radius_expansion_sequence = serializers.ListField(
		child=serializers.DecimalField(max_digits=6, decimal_places=2),
		required=False,
		help_text="Sequence of radii tried during expansion"
	)
	filters_applied = serializers.ListField(
		child=serializers.CharField(),
		help_text="List of filters applied: text, state, geo"
	)
	search_locations = serializers.ListField(
		child=serializers.DictField(),
		help_text="Summary of locations searched"
	)
	performance = serializers.DictField(
		required=False,
		help_text="Search performance metrics"
	)


class BusinessSearchResponseSerializer(serializers.Serializer):
	"""Complete search response with results and metadata."""
	results = BusinessSerializer(many=True)
	search_metadata = SearchMetadataSerializer()


