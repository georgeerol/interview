from rest_framework import serializers
from typing import Dict, Any, List
from decimal import Decimal

from .models import Business
from .constants import US_STATES


class LocationSerializer(serializers.Serializer):
	"""Serializer for individual location filter - either state or lat/lng"""
	state = serializers.CharField(max_length=2, required=False)
	lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
	lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
	
	def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Validate that location has either state OR lat/lng, but not both or neither"""
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
	"""Serializer for business search request validation"""
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
		"""Validate locations array"""
		if not locations:
			raise serializers.ValidationError("At least one location filter is required")
		
		if len(locations) > 20:  # Reasonable limit
			raise serializers.ValidationError("Too many location filters (max 20)")
		
		return locations
	
	def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Cross-field validation"""
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


class BusinessSearchResponseSerializer(serializers.Serializer):
	"""Serializer for business search response with metadata"""
	results = BusinessSerializer(many=True)
	search_metadata = serializers.DictField()


