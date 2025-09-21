"""Unit tests for serializer validation.

Test LocationSerializer and BusinessSearchRequestSerializer validation logic.
"""
from django.test import TestCase
from decimal import Decimal

from core.serializers import BusinessSearchRequestSerializer, LocationSerializer


class LocationSerializerTest(TestCase):
    """Test LocationSerializer validation logic."""

    def test_valid_state_location(self):
        """Test valid state location."""
        data = {"state": "CA"}
        serializer = LocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["state"], "CA")

    def test_valid_state_lowercase(self):
        """Test state gets converted to uppercase."""
        data = {"state": "ca"}
        serializer = LocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["state"], "CA")

    def test_valid_coordinate_location(self):
        """Test valid lat/lng coordinates."""
        data = {"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}
        serializer = LocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["lat"], Decimal("34.052235"))
        self.assertEqual(serializer.validated_data["lng"], Decimal("-118.243683"))

    def test_invalid_state_code(self):
        """Test invalid state code"""
        data = {"state": "ZZ"}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Invalid state code", str(serializer.errors))

    def test_invalid_state_too_long(self):
        """Test state code too long"""
        data = {"state": "CALIFORNIA"}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ensure this field has no more than 2 characters", str(serializer.errors))

    def test_missing_both_state_and_coords(self):
        """Test validation error when neither state nor coordinates provided"""
        data = {}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Location must have either state or lat/lng coordinates", str(serializer.errors))

    def test_both_state_and_coords(self):
        """Test validation error when both state and coordinates provided"""
        data = {"state": "CA", "lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Location cannot have both state and lat/lng coordinates", str(serializer.errors))

    def test_missing_lng(self):
        """Test validation error when lat provided but lng missing"""
        data = {"lat": Decimal("34.052235")}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Location must have either state or lat/lng coordinates", str(serializer.errors))

    def test_missing_lat(self):
        """Test validation error when lng provided but lat missing"""
        data = {"lng": Decimal("-118.243683")}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Location must have either state or lat/lng coordinates", str(serializer.errors))

    def test_invalid_latitude_range(self):
        """Test validation error for latitude out of range"""
        data = {"lat": Decimal("91.0"), "lng": Decimal("-118.243683")}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Latitude must be between -90 and 90", str(serializer.errors))

    def test_invalid_longitude_range(self):
        """Test validation error for longitude out of range"""
        data = {"lat": Decimal("34.052235"), "lng": Decimal("181.0")}
        serializer = LocationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Longitude must be between -180 and 180", str(serializer.errors))


class BusinessSearchRequestSerializerTest(TestCase):
    """Test BusinessSearchRequestSerializer validation logic."""

    def test_valid_state_only_search(self):
        """Test valid search with state only."""
        data = {
            "locations": [{"state": "CA"}],
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["locations"][0]["state"], "CA")
        self.assertEqual(serializer.validated_data["text"], "coffee")

    def test_valid_geo_search_with_explicit_radius(self):
        """Test geo search with explicit radius"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("25.5"),
            "text": "restaurant"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["radius_miles"], Decimal("25.5"))

    def test_valid_geo_search_with_default_radius(self):
        """Test geo search gets default radius when not provided"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["radius_miles"], 50)  # Default radius

    def test_valid_mixed_locations(self):
        """Test valid search with mixed location types"""
        data = {
            "locations": [
                {"state": "CA"},
                {"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}
            ],
            "radius_miles": Decimal("50"),
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_text_allowed(self):
        """Test that missing text is allowed"""
        data = {
            "locations": [{"state": "CA"}]
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_text_allowed(self):
        """Test that empty text is allowed"""
        data = {
            "locations": [{"state": "CA"}],
            "text": ""
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_locations(self):
        """Test validation error for empty locations array"""
        data = {
            "locations": [],
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("At least one location filter is required", str(serializer.errors))

    def test_too_many_locations(self):
        """Test validation error for too many locations"""
        # Use valid state codes to test the location count limit
        states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", 
                 "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI", "OR"]  # 21 states
        data = {
            "locations": [{"state": state} for state in states],
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Too many location filters", str(serializer.errors))

    def test_invalid_radius_too_small(self):
        """Test validation error for radius too small"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("0.05"),  # Below minimum of 0.1
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ensure this value is greater than or equal to 0.1", str(serializer.errors))

    def test_invalid_radius_too_large(self):
        """Test validation error for radius too large"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("1001"),  # Above maximum of 1000
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ensure this value is less than or equal to 1000", str(serializer.errors))
