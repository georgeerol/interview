"""Integration tests for advanced search features.

Test radius expansion, metadata validation, and response structure.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from core.models import Business


class RadiusExpansionTest(APITestCase):
    """Test radius expansion logic."""

    def setUp(self):
        """Set up test data for radius expansion tests."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to isolate our tests
        Business.objects.all().delete()
        
        # Create test businesses at strategic distances for radius expansion testing
        # Point of reference: Las Vegas, NV (36.1699, -115.1398)
        
        # Very close (within 1 mile)
        self.vegas_coffee = Business.objects.create(
            name="Vegas Coffee",
            city="Las Vegas",
            state="NV",
            latitude=Decimal("36.1699"),  # Exact Las Vegas coordinates
            longitude=Decimal("-115.1398")
        )
        
        # Within 10 miles
        self.henderson_books = Business.objects.create(
            name="Henderson Books",
            city="Henderson",
            state="NV", 
            latitude=Decimal("36.0395"),  # ~10 miles from Vegas
            longitude=Decimal("-114.9817")
        )
        
        # Within 50 miles
        self.boulder_city_cafe = Business.objects.create(
            name="Boulder City Cafe",
            city="Boulder City",
            state="NV",
            latitude=Decimal("35.9722"),  # ~30 miles from Vegas
            longitude=Decimal("-114.8324")
        )
        
        # Within 100 miles  
        self.kingman_shop = Business.objects.create(
            name="Kingman Shop",
            city="Kingman",
            state="AZ",
            latitude=Decimal("35.1894"),  # ~90 miles from Vegas
            longitude=Decimal("-114.0531")
        )
        
        # Within 500 miles
        self.phoenix_store = Business.objects.create(
            name="Phoenix Store",
            city="Phoenix", 
            state="AZ",
            latitude=Decimal("33.4484"),  # ~300 miles from Vegas
            longitude=Decimal("-112.0740")
        )
        
        # Very far away (over 500 miles)
        self.denver_market = Business.objects.create(
            name="Denver Market",
            city="Denver",
            state="CO",
            latitude=Decimal("39.7392"),  # ~600+ miles from Vegas
            longitude=Decimal("-104.9903")
        )

    def test_no_expansion_needed(self):
        """Test when initial radius finds results (no expansion needed)."""
        # Search within 50 miles of Vegas - should find results without expansion
        data = {
            "locations": [{"lat": 36.1699, "lng": -115.1398}],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        self.assertGreater(len(results), 0)
        
        # Should find Vegas, Henderson, and Boulder City (3 businesses)
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["radius_used"], 50.0)
        self.assertEqual(metadata["radius_expanded"], False)

    def test_expansion_from_5_to_10(self):
        """Test expansion from 5 miles to 10 miles"""
        # Search within 5 miles - Vegas Coffee is at exact coordinates, so no expansion needed
        data = {
            "locations": [{"lat": 36.1699, "lng": -115.1398}],
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        self.assertGreater(len(results), 0)
        
        metadata = response.data["search_metadata"]
        # Vegas Coffee is at exact coordinates (0 miles), so no expansion needed
        self.assertEqual(metadata["radius_used"], 5.0)
        self.assertEqual(metadata["radius_expanded"], False)

    def test_expansion_from_1_to_first_match(self):
        """Test expansion from 1 mile through sequence until first match"""
        # Search within 1 mile - Vegas Coffee is at exact coordinates (0 miles), so found immediately
        data = {
            "locations": [{"lat": 36.1699, "lng": -115.1398}],
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        self.assertGreater(len(results), 0)
        
        metadata = response.data["search_metadata"]
        # Vegas Coffee is at exact coordinates (0 miles), so no expansion needed
        self.assertEqual(metadata["radius_used"], 1.0)
        self.assertEqual(metadata["radius_expanded"], False)

    def test_expansion_to_max_radius_with_results(self):
        """Test expansion all the way to 500 miles"""
        # Search in middle of desert - should expand until businesses found
        data = {
            "locations": [{"lat": 37.0, "lng": -116.0}],  # Nevada desert
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        self.assertGreater(len(results), 0)  # Should find businesses at some radius
        
        metadata = response.data["search_metadata"]
        # Should expand to find businesses (Kingman is ~100 miles from Vegas, which is ~100 miles from this point)
        self.assertGreater(metadata["radius_used"], 1.0)
        self.assertEqual(metadata["radius_expanded"], True)

    def test_expansion_to_max_radius_no_results(self):
        """Test expansion to 500 miles with no results found"""
        # Clear all businesses to ensure no results
        Business.objects.all().delete()
        
        data = {
            "locations": [{"lat": 37.0, "lng": -116.0}],
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        self.assertEqual(len(results), 0)
        
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["radius_used"], 500.0)  # Tried max radius
        self.assertEqual(metadata["radius_expanded"], True)
        self.assertEqual(metadata["total_count"], 0)

    def test_expansion_with_text_filter(self):
        """Test radius expansion combined with text filtering"""
        data = {
            "locations": [{"lat": 36.1699, "lng": -115.1398}],
            "radius_miles": 1,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        
        if len(results) > 0:
            # Should only return coffee businesses
            for business in results:
                self.assertIn("Coffee", business["name"])
        
        metadata = response.data["search_metadata"]
        self.assertIn("geo", metadata["filters_applied"])
        self.assertIn("text", metadata["filters_applied"])
        # Vegas Coffee is at exact coordinates and matches "coffee", so no expansion needed
        self.assertEqual(metadata["radius_expanded"], False)

    def test_multiple_locations_expansion(self):
        """Test radius expansion with multiple geo locations"""
        data = {
            "locations": [
                {"lat": 37.0, "lng": -116.0},  # Nevada desert
                {"lat": 38.0, "lng": -117.0}   # Another desert point
            ],
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        self.assertIn("geo", metadata["filters_applied"])
        self.assertEqual(metadata["radius_expanded"], True)
        # Should expand through sequence for multiple locations

    def test_readme_example_2_expansion(self):
        """Test the exact README Example 2 scenario"""
        # README Example 2: Nevada desert location with 5-mile initial radius
        data = {
            "locations": [{"lat": 37.9290, "lng": -116.7510}],
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["radius_expanded"], True)
        self.assertGreater(metadata["radius_used"], 5.0)  # Should expand beyond 5
        self.assertIn("geo", metadata["filters_applied"])


class ResponseMetadataTest(APITestCase):
    """Test response format and metadata structure."""

    def setUp(self):
        """Set up test data for metadata tests."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to isolate our tests
        Business.objects.all().delete()
        
        # Create test businesses for comprehensive metadata testing
        self.ca_coffee = Business.objects.create(
            name="CA Coffee Shop",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437")
        )
        
        self.ny_coffee = Business.objects.create(
            name="NY Coffee Bar",
            city="New York",
            state="NY",
            latitude=Decimal("40.7589"),
            longitude=Decimal("-73.9851")
        )
        
        self.tx_restaurant = Business.objects.create(
            name="TX Restaurant",
            city="Austin",
            state="TX",
            latitude=Decimal("30.2672"),
            longitude=Decimal("-97.7431")
        )

    def test_comprehensive_metadata_structure(self):
        """Test that response contains all expected metadata fields"""
        data = {
            "locations": [{"lat": 34.0522, "lng": -118.2437}],
            "radius_miles": 50,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check main response structure
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        
        metadata = response.data["search_metadata"]
        
        # Check all required metadata fields
        required_fields = [
            "total_count", "total_found", "radius_used", "radius_expanded",
            "filters_applied", "search_locations"
        ]
        for field in required_fields:
            self.assertIn(field, metadata, f"Missing required field: {field}")
        
        # Check geo-specific fields
        self.assertIn("radius_requested", metadata)
        
        # Check data types
        self.assertIsInstance(metadata["total_count"], int)
        self.assertIsInstance(metadata["total_found"], int)
        self.assertIsInstance(metadata["radius_used"], float)
        self.assertIsInstance(metadata["radius_expanded"], bool)
        self.assertIsInstance(metadata["filters_applied"], list)
        self.assertIsInstance(metadata["search_locations"], list)

    def test_search_locations_summary_state(self):
        """Test search_locations summary for state-based searches"""
        data = {
            "locations": [{"state": "CA"}, {"state": "NY"}],
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        locations = metadata["search_locations"]
        
        self.assertEqual(len(locations), 2)
        
        # Check state location format
        state_locations = [loc for loc in locations if loc["type"] == "state"]
        self.assertEqual(len(state_locations), 2)
        
        states = {loc["state"] for loc in state_locations}
        self.assertEqual(states, {"CA", "NY"})

    def test_search_locations_summary_geo(self):
        """Test search_locations summary for geo-based searches"""
        data = {
            "locations": [
                {"lat": 34.0522, "lng": -118.2437},
                {"lat": 40.7589, "lng": -73.9851}
            ],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        locations = metadata["search_locations"]
        
        self.assertEqual(len(locations), 2)
        
        # Check geo location format
        geo_locations = [loc for loc in locations if loc["type"] == "geo"]
        self.assertEqual(len(geo_locations), 2)
        
        # Check coordinates are properly formatted
        for geo_loc in geo_locations:
            self.assertIn("lat", geo_loc)
            self.assertIn("lng", geo_loc)
            self.assertIsInstance(geo_loc["lat"], float)
            self.assertIsInstance(geo_loc["lng"], float)

    def test_search_locations_summary_mixed(self):
        """Test search_locations summary for mixed state/geo searches"""
        data = {
            "locations": [
                {"state": "TX"},
                {"lat": 34.0522, "lng": -118.2437}
            ],
            "radius_miles": 1000
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        locations = metadata["search_locations"]
        
        self.assertEqual(len(locations), 2)
        
        # Should have one state and one geo location
        types = [loc["type"] for loc in locations]
        self.assertIn("state", types)
        self.assertIn("geo", types)

    def test_radius_expansion_sequence_tracking(self):
        """Test that radius_expansion_sequence is properly tracked"""
        data = {
            "locations": [{"lat": 37.0, "lng": -116.0}],  # Nevada desert
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        if metadata["radius_expanded"]:
            # Should have radius_expansion_sequence
            self.assertIn("radius_expansion_sequence", metadata)
            sequence = metadata["radius_expansion_sequence"]
            
            # Should start with requested radius
            self.assertEqual(sequence[0], 1.0)
            
            # Should be in ascending order
            self.assertEqual(sequence, sorted(sequence))
            
            # Final radius should match radius_used
            self.assertEqual(sequence[-1], metadata["radius_used"])

    def test_filters_applied_tracking(self):
        """Test that filters_applied correctly tracks all applied filters"""
        # Test with all three filter types
        data = {
            "locations": [
                {"state": "CA"},
                {"lat": 40.7589, "lng": -73.9851}
            ],
            "radius_miles": 50,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        filters = metadata["filters_applied"]
        
        # Should include all three filter types
        self.assertIn("text", filters)
        self.assertIn("state", filters)
        self.assertIn("geo", filters)

    def test_total_count_vs_total_found(self):
        """Test the distinction between total_count and total_found"""
        # This test assumes we might have pagination in the future
        data = {
            "locations": [{"state": "CA"}]
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        results = response.data["results"]
        
        # total_count should match actual returned results
        self.assertEqual(metadata["total_count"], len(results))
        
        # total_found should be >= total_count (could be more if pagination)
        self.assertGreaterEqual(metadata["total_found"], metadata["total_count"])

    def test_radius_metadata_only_for_geo_searches(self):
        """Test that radius metadata only appears for geo searches"""
        # State-only search
        data = {
            "locations": [{"state": "CA"}],
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        # Should not have radius-specific fields
        self.assertNotIn("radius_requested", metadata)
        self.assertNotIn("radius_expansion_sequence", metadata)
        
        # But should have radius_used and radius_expanded (default values)
        self.assertIn("radius_used", metadata)
        self.assertIn("radius_expanded", metadata)

    def test_readme_example_1_comprehensive_metadata(self):
        """Test comprehensive metadata for README Example 1"""
        data = {
            "locations": [
                {"state": "NY"},
                {"state": "CA"},
                {"lat": 34.052235, "lng": -118.243683}
            ],
            "text": "coffee",
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        # Check comprehensive structure
        self.assertIn("total_count", metadata)
        self.assertIn("total_found", metadata)
        self.assertIn("radius_requested", metadata)
        self.assertEqual(metadata["radius_requested"], 50.0)
        
        # Should have all three filter types
        filters = metadata["filters_applied"]
        self.assertIn("text", filters)
        self.assertIn("state", filters)
        self.assertIn("geo", filters)
        
        # Should have 3 search locations (2 states + 1 geo)
        locations = metadata["search_locations"]
        self.assertEqual(len(locations), 3)
        
        # Check location types
        types = [loc["type"] for loc in locations]
        self.assertEqual(types.count("state"), 2)
        self.assertEqual(types.count("geo"), 1)

    def test_readme_example_2_comprehensive_metadata(self):
        """Test comprehensive metadata for README Example 2"""
        data = {
            "locations": [{"lat": 37.9290, "lng": -116.7510}],
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        # Should show radius expansion
        self.assertEqual(metadata["radius_requested"], 5.0)
        self.assertGreater(metadata["radius_used"], 5.0)
        self.assertEqual(metadata["radius_expanded"], True)
        
        # Should have expansion sequence
        self.assertIn("radius_expansion_sequence", metadata)
        sequence = metadata["radius_expansion_sequence"]
        self.assertEqual(sequence[0], 5.0)  # Started with 5
        self.assertGreater(len(sequence), 1)  # Expanded through multiple radii
        
        # Should have single geo location
        locations = metadata["search_locations"]
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]["type"], "geo")
        self.assertEqual(locations[0]["lat"], 37.9290)
        self.assertEqual(locations[0]["lng"], -116.7510)
