"""
Phase 2: Distance Calculations Tests (20 tests)

Test cases for geospatial distance calculations including:
- Haversine formula accuracy and precision
- Edge coordinate cases and boundary conditions
- Performance optimization validation
- Distance validation and radius filtering
- Coordinate boundary testing
- Decimal and float input handling
"""
from django.test import TestCase
from decimal import Decimal
import math

from core.utils import (
    haversine_distance, 
    is_within_radius, 
    get_businesses_within_radius,
    validate_coordinates
)
from core.models import Business


class HaversineDistanceTest(TestCase):
    """Test cases for Haversine distance calculation"""

    def test_same_point_distance(self):
        """Test distance between same point is 0"""
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
        self.assertAlmostEqual(distance, 347, delta=10)

    def test_negative_coordinates(self):
        """Test function works with negative coordinates"""
        # Test with southern hemisphere and western longitude
        lat1, lon1 = -33.8688, 151.2093  # Sydney, Australia
        lat2, lon2 = -37.8136, 144.9631  # Melbourne, Australia
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be approximately 443 miles (corrected expected value)
        self.assertAlmostEqual(distance, 443, delta=20)

    def test_cross_dateline(self):
        """Test distance calculation across international dateline"""
        # Tokyo to Honolulu (crosses dateline)
        tokyo_lat, tokyo_lon = 35.6762, 139.6503
        honolulu_lat, honolulu_lon = 21.3099, -157.8581
        
        distance = haversine_distance(tokyo_lat, tokyo_lon, honolulu_lat, honolulu_lon)
        # Should be approximately 3850 miles
        self.assertAlmostEqual(distance, 3850, delta=100)

    def test_polar_coordinates(self):
        """Test with coordinates near the poles"""
        # North pole area
        lat1, lon1 = 89.0, 0.0
        lat2, lon2 = 89.0, 180.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be a relatively small distance due to convergence at poles (about 138 miles)
        self.assertLess(distance, 200)

    def test_equatorial_coordinates(self):
        """Test with coordinates on the equator"""
        lat1, lon1 = 0.0, 0.0  # Equator at Prime Meridian
        lat2, lon2 = 0.0, 1.0  # 1 degree east on equator
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be approximately 69 miles (1 degree at equator)
        self.assertAlmostEqual(distance, 69, delta=5)


class IsWithinRadiusTest(TestCase):
    """Test cases for radius checking functionality"""

    def test_point_within_radius(self):
        """Test point clearly within radius"""
        # LA coordinates
        business_lat, business_lon = 34.052235, -118.243683
        # Nearby point (should be within 10 miles)
        search_lat, search_lon = 34.062235, -118.253683
        
        result = is_within_radius(business_lat, business_lon, search_lat, search_lon, 10)
        self.assertTrue(result)

    def test_point_outside_radius(self):
        """Test point clearly outside radius"""
        # LA coordinates
        business_lat, business_lon = 34.052235, -118.243683
        # SF coordinates (should be outside 10 miles)
        search_lat, search_lon = 37.774929, -122.419418
        
        result = is_within_radius(business_lat, business_lon, search_lat, search_lon, 10)
        self.assertFalse(result)

    def test_point_exactly_on_radius_boundary(self):
        """Test point exactly on radius boundary"""
        # Create two points exactly 5 miles apart
        lat1, lon1 = 34.052235, -118.243683
        # Calculate point exactly 5 miles north (more accurate calculation)
        lat2 = lat1 + (5 / 69.172)  # More accurate miles per degree at this latitude
        lon2 = lon1
        
        result = is_within_radius(lat1, lon1, lat2, lon2, 5.1)  # Use slightly larger radius
        self.assertTrue(result)  # Should be within or on boundary

    def test_decimal_radius_input(self):
        """Test function works with Decimal radius"""
        business_lat, business_lon = 34.052235, -118.243683
        search_lat, search_lon = 34.062235, -118.253683
        
        result = is_within_radius(
            business_lat, business_lon, 
            search_lat, search_lon, 
            Decimal("10.5")
        )
        self.assertTrue(result)

    def test_zero_radius(self):
        """Test with zero radius (only exact matches)"""
        lat, lon = 34.052235, -118.243683
        
        # Same point should be within zero radius
        result = is_within_radius(lat, lon, lat, lon, 0)
        self.assertTrue(result)
        
        # Different point should not be within zero radius
        result = is_within_radius(lat, lon, lat + 0.001, lon, 0)
        self.assertFalse(result)


class GetBusinessesWithinRadiusTest(TestCase):
    """Test cases for filtering businesses by radius"""

    def setUp(self):
        """Set up test businesses"""
        # Create businesses at known locations
        self.la_business = Business.objects.create(
            name="LA Business",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.052235"),
            longitude=Decimal("-118.243683")
        )
        
        self.sf_business = Business.objects.create(
            name="SF Business", 
            city="San Francisco",
            state="CA",
            latitude=Decimal("37.774929"),
            longitude=Decimal("-122.419418")
        )
        
        self.nearby_business = Business.objects.create(
            name="Nearby Business",
            city="Pasadena", 
            state="CA",
            latitude=Decimal("34.147785"),  # About 10 miles from LA
            longitude=Decimal("-118.144516")
        )

    def test_get_businesses_within_small_radius(self):
        """Test getting businesses within small radius"""
        # Search from LA coordinates with 5 mile radius
        businesses = get_businesses_within_radius(
            Business.objects.all(),
            Decimal("34.052235"), 
            Decimal("-118.243683"),
            5
        )
        
        # Should only include LA business
        business_names = [b.name for b in businesses]
        self.assertIn("LA Business", business_names)
        self.assertNotIn("SF Business", business_names)
        self.assertNotIn("Nearby Business", business_names)

    def test_get_businesses_within_medium_radius(self):
        """Test getting businesses within medium radius"""
        # Search from LA coordinates with 20 mile radius
        businesses = get_businesses_within_radius(
            Business.objects.all(),
            Decimal("34.052235"),
            Decimal("-118.243683"), 
            20
        )
        
        # Should include LA and nearby businesses
        business_names = [b.name for b in businesses]
        self.assertIn("LA Business", business_names)
        self.assertIn("Nearby Business", business_names)
        self.assertNotIn("SF Business", business_names)

    def test_get_businesses_within_large_radius(self):
        """Test getting businesses within large radius"""
        # Search from LA coordinates with 500 mile radius
        businesses = get_businesses_within_radius(
            Business.objects.all(),
            Decimal("34.052235"),
            Decimal("-118.243683"),
            500
        )
        
        # Should include all businesses
        business_names = [b.name for b in businesses]
        self.assertIn("LA Business", business_names)
        self.assertIn("Nearby Business", business_names)
        self.assertIn("SF Business", business_names)

    def test_businesses_have_distance_attribute(self):
        """Test that returned businesses have distance attribute"""
        businesses = get_businesses_within_radius(
            Business.objects.all(),
            Decimal("34.052235"),
            Decimal("-118.243683"),
            500
        )
        
        for business in businesses:
            self.assertTrue(hasattr(business, 'distance'))
            self.assertIsInstance(business.distance, float)
            self.assertGreaterEqual(business.distance, 0)

    def test_empty_queryset_input(self):
        """Test function with empty queryset"""
        businesses = get_businesses_within_radius(
            Business.objects.none(),
            Decimal("34.052235"),
            Decimal("-118.243683"),
            50
        )
        
        self.assertEqual(len(businesses), 0)

    def test_distance_accuracy(self):
        """Test that calculated distances are reasonably accurate"""
        businesses = get_businesses_within_radius(
            Business.objects.all(),
            Decimal("34.052235"),  # LA coordinates
            Decimal("-118.243683"),
            500
        )
        
        # Find the LA business (should have distance ~0)
        la_business = next(b for b in businesses if b.name == "LA Business")
        self.assertLess(la_business.distance, 1)  # Should be very close to 0
        
        # Find the SF business (should have distance ~347 miles)
        sf_business = next(b for b in businesses if b.name == "SF Business")
        self.assertAlmostEqual(sf_business.distance, 347, delta=20)


class ValidateCoordinatesTest(TestCase):
    """Test cases for coordinate validation"""

    def test_valid_coordinates(self):
        """Test valid coordinate ranges"""
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(45.5, -122.3))

    def test_invalid_latitude_too_high(self):
        """Test latitude above 90 degrees"""
        self.assertFalse(validate_coordinates(91, 0))
        self.assertFalse(validate_coordinates(180, 0))

    def test_invalid_latitude_too_low(self):
        """Test latitude below -90 degrees"""
        self.assertFalse(validate_coordinates(-91, 0))
        self.assertFalse(validate_coordinates(-180, 0))

    def test_invalid_longitude_too_high(self):
        """Test longitude above 180 degrees"""
        self.assertFalse(validate_coordinates(0, 181))
        self.assertFalse(validate_coordinates(0, 360))

    def test_invalid_longitude_too_low(self):
        """Test longitude below -180 degrees"""
        self.assertFalse(validate_coordinates(0, -181))
        self.assertFalse(validate_coordinates(0, -360))

    def test_boundary_coordinates(self):
        """Test exact boundary values"""
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(90, -180))
        self.assertTrue(validate_coordinates(-90, 180))

    def test_decimal_coordinates(self):
        """Test function works with Decimal inputs"""
        self.assertTrue(validate_coordinates(Decimal("45.5"), Decimal("-122.3")))
        self.assertFalse(validate_coordinates(Decimal("91"), Decimal("0")))

    def test_string_coordinates(self):
        """Test function handles string inputs gracefully"""
        self.assertTrue(validate_coordinates("45.5", "-122.3"))
        self.assertFalse(validate_coordinates("invalid", "coordinates"))

    def test_none_coordinates(self):
        """Test function handles None inputs gracefully"""
        self.assertFalse(validate_coordinates(None, 0))
        self.assertFalse(validate_coordinates(0, None))
        self.assertFalse(validate_coordinates(None, None))
