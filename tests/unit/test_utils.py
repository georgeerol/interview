"""Unit tests for utility functions.

Test distance calculations, coordinate validation, and radius filtering.
"""
from django.test import TestCase
from decimal import Decimal
import math

from core.infrastructure import (
    haversine_distance, 
    is_within_radius, 
    get_businesses_within_radius,
    validate_coordinates
)
from core.domain import Business


class HaversineDistanceTest(TestCase):
    """Test Haversine distance calculation."""

    def test_same_point_distance(self):
        """Test distance between same point is 0."""
        lat, lon = 34.052235, -118.243683
        distance = haversine_distance(lat, lon, lat, lon)
        self.assertAlmostEqual(distance, 0, places=2)

    def test_known_distance_la_to_sf(self):
        """Test known distance: LA to San Francisco (~347 miles)"""
        # Los Angeles coordinates
        la_lat, la_lon = 34.052235, -118.243683
        # San Francisco coordinates  
        sf_lat, sf_lon = 37.774929, -122.419418
        
        distance = haversine_distance(la_lat, la_lon, sf_lat, sf_lon)
        # Should be approximately 347 miles
        self.assertAlmostEqual(distance, 347, delta=10)

    def test_known_distance_ny_to_la(self):
        """Test known distance: NYC to LA (~2445 miles)"""
        # New York coordinates
        ny_lat, ny_lon = 40.712776, -74.005974
        # Los Angeles coordinates
        la_lat, la_lon = 34.052235, -118.243683
        
        distance = haversine_distance(ny_lat, ny_lon, la_lat, la_lon)
        # Should be approximately 2445 miles
        self.assertAlmostEqual(distance, 2445, delta=50)

    def test_decimal_inputs(self):
        """Test function works with Decimal inputs"""
        lat1, lon1 = Decimal("34.052235"), Decimal("-118.243683")
        lat2, lon2 = Decimal("37.774929"), Decimal("-122.419418")
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertIsInstance(distance, float)
        self.assertAlmostEqual(distance, 347, delta=10)

    def test_negative_coordinates(self):
        """Test function works with negative coordinates"""
        # Test points in different hemispheres
        lat1, lon1 = -33.8688, 151.2093  # Sydney, Australia
        lat2, lon2 = 51.5074, -0.1278    # London, UK
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be approximately 10,500+ miles
        self.assertGreater(distance, 10000)

    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (within a city)"""
        # Two points in downtown LA, about 1 mile apart
        lat1, lon1 = 34.052235, -118.243683  # Downtown LA
        lat2, lon2 = 34.061928, -118.248071  # Hollywood & Highland
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be approximately 1-2 miles
        self.assertLess(distance, 5)
        self.assertGreater(distance, 0.5)


class IsWithinRadiusTest(TestCase):
    """Test is_within_radius function."""

    def test_point_within_radius(self):
        """Test point within radius returns True"""
        center_lat, center_lon = 34.052235, -118.243683
        # Point 1 mile away
        test_lat, test_lon = 34.061928, -118.248071
        
        result = is_within_radius(test_lat, test_lon, center_lat, center_lon, 5)
        self.assertTrue(result)

    def test_point_outside_radius(self):
        """Test point outside radius returns False"""
        center_lat, center_lon = 34.052235, -118.243683  # LA
        test_lat, test_lon = 37.774929, -122.419418      # SF
        
        result = is_within_radius(test_lat, test_lon, center_lat, center_lon, 100)
        self.assertFalse(result)  # SF is ~347 miles from LA

    def test_point_exactly_on_radius(self):
        """Test point exactly on radius boundary"""
        center_lat, center_lon = 34.052235, -118.243683
        test_lat, test_lon = 34.052235, -118.243683  # Same point
        
        result = is_within_radius(test_lat, test_lon, center_lat, center_lon, 0)
        self.assertTrue(result)  # Distance is 0, radius is 0

    def test_decimal_radius(self):
        """Test function works with decimal radius"""
        center_lat, center_lon = 34.052235, -118.243683
        test_lat, test_lon = 34.061928, -118.248071
        
        result = is_within_radius(test_lat, test_lon, center_lat, center_lon, Decimal("5.5"))
        self.assertTrue(result)


class GetBusinessesWithinRadiusTest(TestCase):
    """Test get_businesses_within_radius function."""

    def setUp(self):
        """Set up test businesses."""
        # Clear existing businesses to isolate our tests
        Business.objects.all().delete()
        
        # Create businesses at known locations
        self.la_business = Business.objects.create(
            name="LA Coffee",
            city="Los Angeles", 
            state="CA",
            latitude=Decimal("34.052235"),
            longitude=Decimal("-118.243683")
        )
        
        self.sf_business = Business.objects.create(
            name="SF Coffee",
            city="San Francisco",
            state="CA", 
            latitude=Decimal("37.774929"),
            longitude=Decimal("-122.419418")
        )
        
        self.ny_business = Business.objects.create(
            name="NY Coffee",
            city="New York",
            state="NY",
            latitude=Decimal("40.712776"),
            longitude=Decimal("-74.005974")
        )

    def test_businesses_within_small_radius(self):
        """Test finding businesses within small radius"""
        search_lat, search_lon = 34.052235, -118.243683  # LA coordinates
        radius = 50  # 50 miles
        
        businesses = Business.objects.all()
        result = get_businesses_within_radius(businesses, search_lat, search_lon, radius)
        
        # Only LA business should be within 50 miles of LA
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "LA Coffee")
        self.assertTrue(hasattr(result[0], 'distance'))
        self.assertAlmostEqual(result[0].distance, 0, places=1)

    def test_businesses_within_large_radius(self):
        """Test finding businesses within large radius"""
        search_lat, search_lon = 34.052235, -118.243683  # LA coordinates  
        radius = 500  # 500 miles
        
        businesses = Business.objects.all()
        result = get_businesses_within_radius(businesses, search_lat, search_lon, radius)
        
        # LA and SF should be within 500 miles, but not NY
        self.assertEqual(len(result), 2)
        business_names = [b.name for b in result]
        self.assertIn("LA Coffee", business_names)
        self.assertIn("SF Coffee", business_names)
        self.assertNotIn("NY Coffee", business_names)

    def test_businesses_within_very_large_radius(self):
        """Test finding businesses within very large radius"""
        search_lat, search_lon = 34.052235, -118.243683  # LA coordinates
        radius = 3000  # 3000 miles (coast to coast)
        
        businesses = Business.objects.all()
        result = get_businesses_within_radius(businesses, search_lat, search_lon, radius)
        
        # All businesses should be within 3000 miles
        self.assertEqual(len(result), 3)
        business_names = [b.name for b in result]
        self.assertIn("LA Coffee", business_names)
        self.assertIn("SF Coffee", business_names) 
        self.assertIn("NY Coffee", business_names)

    def test_no_businesses_within_radius(self):
        """Test when no businesses are within radius"""
        # Search in middle of Nevada desert
        search_lat, search_lon = 37.9290, -116.7510
        radius = 1  # 1 mile
        
        businesses = Business.objects.all()
        result = get_businesses_within_radius(businesses, search_lat, search_lon, radius)
        
        self.assertEqual(len(result), 0)

    def test_distance_attribute_added(self):
        """Test that distance attribute is added to businesses"""
        search_lat, search_lon = 34.052235, -118.243683  # LA coordinates
        radius = 500  # 500 miles
        
        businesses = Business.objects.all()
        result = get_businesses_within_radius(businesses, search_lat, search_lon, radius)
        
        for business in result:
            self.assertTrue(hasattr(business, 'distance'))
            self.assertIsInstance(business.distance, float)
            self.assertGreaterEqual(business.distance, 0)


class ValidateCoordinatesTest(TestCase):
    """Test coordinate validation."""

    def test_valid_coordinates(self):
        """Test valid coordinate ranges"""
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(34.052235, -118.243683))

    def test_invalid_latitude(self):
        """Test invalid latitude values"""
        self.assertFalse(validate_coordinates(91, 0))    # Too high
        self.assertFalse(validate_coordinates(-91, 0))   # Too low
        self.assertFalse(validate_coordinates(100, 0))   # Way too high

    def test_invalid_longitude(self):
        """Test invalid longitude values"""
        self.assertFalse(validate_coordinates(0, 181))   # Too high
        self.assertFalse(validate_coordinates(0, -181))  # Too low
        self.assertFalse(validate_coordinates(0, 200))   # Way too high

    def test_decimal_coordinates(self):
        """Test validation works with Decimal inputs"""
        self.assertTrue(validate_coordinates(Decimal("34.052235"), Decimal("-118.243683")))
        self.assertFalse(validate_coordinates(Decimal("91"), Decimal("0")))

    def test_invalid_types(self):
        """Test validation handles invalid types"""
        self.assertFalse(validate_coordinates("invalid", 0))
        self.assertFalse(validate_coordinates(0, "invalid"))
        self.assertFalse(validate_coordinates(None, 0))
        self.assertFalse(validate_coordinates(0, None))
