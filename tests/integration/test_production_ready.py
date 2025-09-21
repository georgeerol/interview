"""Integration tests for production-ready features.

Test edge cases, caching, error handling, performance monitoring, and README examples.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from core.domain import Business


class EdgeCaseAndBoundaryTest(APITestCase):
    """Test comprehensive edge cases and README examples."""

    def setUp(self):
        """Set up test data for edge case testing."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to have controlled test data
        Business.objects.all().delete()
        
        # Create comprehensive test dataset covering all scenarios
        
        # California businesses for README Example 1
        self.ca_businesses = [
            Business.objects.create(
                name="Prime Coffee & Co", city="San Francisco", state="CA",
                latitude=Decimal("37.7749"), longitude=Decimal("-122.4194")
            ),
            Business.objects.create(
                name="Urban Coffee LLC", city="Los Angeles", state="CA", 
                latitude=Decimal("34.0522"), longitude=Decimal("-118.2437")  # Exact README coordinates
            ),
            Business.objects.create(
                name="Golden Coffee Shop", city="San Diego", state="CA",
                latitude=Decimal("32.7157"), longitude=Decimal("-117.1611")
            ),
            Business.objects.create(
                name="CA Restaurant", city="Sacramento", state="CA",  # Non-coffee business
                latitude=Decimal("38.5816"), longitude=Decimal("-121.4944")
            ),
        ]
        
        # New York businesses for README Example 1
        self.ny_businesses = [
            Business.objects.create(
                name="NY Coffee Bar", city="New York", state="NY",
                latitude=Decimal("40.7128"), longitude=Decimal("-74.0060")
            ),
            Business.objects.create(
                name="Buffalo Coffee House", city="Buffalo", state="NY",
                latitude=Decimal("42.8864"), longitude=Decimal("-78.8784")
            ),
            Business.objects.create(
                name="NY Deli", city="Albany", state="NY",  # Non-coffee business
                latitude=Decimal("42.6526"), longitude=Decimal("-73.7562")
            ),
        ]
        
        # Texas businesses (outside CA/NY for testing exclusion)
        self.tx_businesses = [
            Business.objects.create(
                name="Austin Coffee Co", city="Austin", state="TX",
                latitude=Decimal("30.2672"), longitude=Decimal("-97.7431")
            ),
            Business.objects.create(
                name="Dallas Coffee Shop", city="Dallas", state="TX",
                latitude=Decimal("32.7767"), longitude=Decimal("-96.7970")
            ),
        ]

    def test_readme_example_1_exact_implementation(self):
        """Test exact README Example 1 with comprehensive validation."""
        data = {
            "locations": [
                {"state": "CA"},
                {"state": "NY"}, 
                {"lat": 34.052235, "lng": -118.243683}  # Exact README coordinates (LA)
            ],
            "text": "coffee",
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        metadata = response.data["search_metadata"]
        
        # Validate comprehensive response structure
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        
        # Validate metadata completeness
        required_metadata = [
            "total_count", "total_found", "radius_used", "radius_expanded",
            "filters_applied", "search_locations", "radius_requested"
        ]
        for field in required_metadata:
            self.assertIn(field, metadata)
        
        # Validate filters applied
        self.assertIn("text", metadata["filters_applied"])
        self.assertIn("state", metadata["filters_applied"]) 
        self.assertIn("geo", metadata["filters_applied"])
        
        # Validate search locations
        locations = metadata["search_locations"]
        self.assertEqual(len(locations), 3)
        
        location_types = [loc["type"] for loc in locations]
        self.assertEqual(location_types.count("state"), 2)
        self.assertEqual(location_types.count("geo"), 1)
        
        # Validate business results contain only coffee businesses
        business_names = [b["name"] for b in results]
        for name in business_names:
            self.assertIn("Coffee", name, f"Non-coffee business returned: {name}")

    def test_readme_example_2_exact_implementation(self):
        """Test exact README Example 2 with radius expansion validation."""
        data = {
            "locations": [{"lat": 37.9290, "lng": -116.7510}],  # Exact README coordinates (Nevada desert)
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        metadata = response.data["search_metadata"]
        
        # Should demonstrate radius expansion
        self.assertEqual(metadata["radius_requested"], 5.0)
        self.assertGreater(metadata["radius_used"], 5.0)
        self.assertEqual(metadata["radius_expanded"], True)
        
        # Should have expansion sequence
        self.assertIn("radius_expansion_sequence", metadata)
        sequence = metadata["radius_expansion_sequence"]
        
        # Sequence should start with 5 and expand through the defined sequence
        self.assertEqual(sequence[0], 5.0)
        self.assertGreater(len(sequence), 1)
        
        # All radii in sequence should be from the expansion sequence [1,5,10,25,50,100,500]
        valid_radii = {1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 500.0}
        for radius in sequence:
            self.assertIn(radius, valid_radii)
        
        # Should be in ascending order
        self.assertEqual(sequence, sorted(sequence))
        
        # Final radius should match radius_used
        self.assertEqual(sequence[-1], metadata["radius_used"])

    def test_edge_case_maximum_locations(self):
        """Test maximum number of locations (20 per validation)."""
        # Create 20 different state locations (max allowed)
        states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", 
                 "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI"]
        
        locations = [{"state": state} for state in states]
        
        data = {
            "locations": locations,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        self.assertEqual(len(metadata["search_locations"]), 20)
        self.assertIn("state", metadata["filters_applied"])

    def test_edge_case_maximum_locations_plus_one(self):
        """Test exceeding maximum locations (21 locations should fail)."""
        states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", 
                 "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI", "OR"]  # 21 states
        
        locations = [{"state": state} for state in states]
        
        data = {
            "locations": locations,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_edge_case_boundary_radius_values(self):
        """Test boundary radius values (0.1, 1000.0)."""
        # Test minimum radius
        data = {
            "locations": [{"lat": 34.0522, "lng": -118.2437}],
            "radius_miles": 0.1  # Minimum allowed
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test maximum radius
        data = {
            "locations": [{"lat": 34.0522, "lng": -118.2437}],
            "radius_miles": 1000.0  # Maximum allowed
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test over maximum radius (should fail)
        data = {
            "locations": [{"lat": 34.0522, "lng": -118.2437}],
            "radius_miles": 1001.0  # Over maximum
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edge_case_coordinate_boundaries(self):
        """Test coordinate boundary values."""
        # Test extreme valid coordinates
        boundary_coords = [
            {"lat": 90.0, "lng": 180.0},     # North pole, international date line
            {"lat": -90.0, "lng": -180.0},   # South pole, opposite date line
            {"lat": 0.0, "lng": 0.0},        # Null island
        ]
        
        for coords in boundary_coords:
            data = {
                "locations": [coords],
                "radius_miles": 50
            }
            response = self.client.post(self.search_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK, 
                           f"Failed for coordinates: {coords}")

    def test_edge_case_invalid_coordinates(self):
        """Test invalid coordinate values."""
        invalid_coords = [
            {"lat": 91.0, "lng": 0.0},       # Latitude too high
            {"lat": -91.0, "lng": 0.0},      # Latitude too low
            {"lat": 0.0, "lng": 181.0},      # Longitude too high
            {"lat": 0.0, "lng": -181.0},     # Longitude too low
        ]
        
        for coords in invalid_coords:
            data = {
                "locations": [coords],
                "radius_miles": 50
            }
            response = self.client.post(self.search_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Should have failed for coordinates: {coords}")

    def test_edge_case_empty_text_search(self):
        """Test empty and whitespace-only text searches."""
        # Test valid empty/whitespace text values
        test_texts = ["", "   ", "\t\n"]
        
        for text in test_texts:
            data = {
                "locations": [{"state": "CA"}],
                "text": text
            }
            response = self.client.post(self.search_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should not have text in filters_applied for empty/whitespace text
            metadata = response.data["search_metadata"]
            if not text or not text.strip():
                self.assertNotIn("text", metadata["filters_applied"])

    def test_edge_case_case_insensitive_text_search(self):
        """Test case insensitive text searching."""
        variations = ["coffee", "COFFEE", "Coffee", "CoFfEe", "cOfFeE"]
        
        base_data = {
            "locations": [{"state": "CA"}],
            "radius_miles": 50
        }
        
        expected_results = None
        
        for variation in variations:
            data = {**base_data, "text": variation}
            response = self.client.post(self.search_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            results = response.data["results"]
            
            if expected_results is None:
                expected_results = {r["id"] for r in results}
            else:
                current_results = {r["id"] for r in results}
                self.assertEqual(expected_results, current_results, 
                               f"Case variation '{variation}' returned different results")

    def test_edge_case_duplicate_locations(self):
        """Test duplicate location handling."""
        data = {
            "locations": [
                {"state": "CA"},
                {"state": "CA"},  # Duplicate state
                {"lat": 34.0522, "lng": -118.2437},
                {"lat": 34.0522, "lng": -118.2437}  # Duplicate coordinates
            ],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should handle duplicates gracefully
        results = response.data["results"]
        business_ids = [r["id"] for r in results]
        
        # Should not have duplicate businesses in results
        self.assertEqual(len(business_ids), len(set(business_ids)), 
                        "Duplicate businesses found in results")

    def test_performance_large_result_set(self):
        """Test performance with large result sets (pagination behavior)."""
        # Search that should return many results
        data = {
            "locations": [{"state": "CA"}, {"state": "NY"}, {"state": "TX"}],
            # No text filter to get more results
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data["results"]
        metadata = response.data["search_metadata"]
        
        # Should limit results to 100 (current implementation)
        self.assertLessEqual(len(results), 100)
        self.assertLessEqual(metadata["total_count"], 100)
        
        # total_found might be higher than total_count (indicating more results available)
        self.assertGreaterEqual(metadata["total_found"], metadata["total_count"])


class ProductionPerformanceTest(APITestCase):
    """Test performance optimization and production features."""

    def setUp(self):
        """Set up test data for performance testing."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to have controlled test data
        Business.objects.all().delete()
        
        # Create test businesses for performance testing
        self.test_businesses = []
        for i in range(20):
            business = Business.objects.create(
                name=f"Test Business {i}",
                city=f"City {i}",
                state="CA",
                latitude=Decimal("34.0522"),
                longitude=Decimal("-118.2437")
            )
            self.test_businesses.append(business)

    def test_performance_metadata_included(self):
        """Test that performance metadata is included in responses."""
        data = {
            "locations": [{"state": "CA"}],
            "text": "test"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        # Check performance metadata exists
        self.assertIn("performance", metadata)
        performance = metadata["performance"]
        
        # Check performance fields
        self.assertIn("processing_time_ms", performance)
        self.assertIn("search_id", performance)
        self.assertIn("cached", performance)
        
        # Validate data types
        self.assertIsInstance(performance["processing_time_ms"], (int, float))
        self.assertIsInstance(performance["search_id"], str)
        self.assertIsInstance(performance["cached"], bool)
        
        # Should not be cached on first request
        self.assertEqual(performance["cached"], False)

    def test_caching_functionality(self):
        """Test that search results are properly cached."""
        data = {
            "locations": [{"state": "CA"}],
            "text": "test"
        }
        
        # First request - should not be cached
        response1 = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        performance1 = response1.data["search_metadata"]["performance"]
        self.assertEqual(performance1["cached"], False)
        
        # Second identical request - should be cached
        response2 = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        performance2 = response2.data["search_metadata"]["performance"]
        self.assertEqual(performance2["cached"], True)
        
        # Results should be identical
        self.assertEqual(
            response1.data["results"], 
            response2.data["results"]
        )
        
        # Cache metadata should be present
        self.assertIn("cache_key", response2.data["search_metadata"])

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        # Identical requests should generate same cache key
        data1 = {
            "locations": [{"state": "CA"}, {"state": "NY"}],
            "text": "coffee",
            "radius_miles": 50
        }
        
        data2 = {
            "locations": [{"state": "NY"}, {"state": "CA"}],  # Different order
            "text": "coffee",
            "radius_miles": 50
        }
        
        response1 = self.client.post(self.search_url, data1, format='json')
        response2 = self.client.post(self.search_url, data2, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Second request should be cached (same normalized request)
        performance2 = response2.data["search_metadata"]["performance"]
        self.assertEqual(performance2["cached"], True)

    def test_error_handling_with_logging(self):
        """Test production error handling and logging."""
        # Test with malformed request
        response = self.client.post(self.search_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("details", response.data)

    def test_search_id_generation(self):
        """Test that unique search IDs are generated."""
        data = {"locations": [{"state": "CA"}]}
        
        response1 = self.client.post(self.search_url, data, format='json')
        response2 = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        search_id1 = response1.data["search_metadata"]["performance"]["search_id"]
        search_id2 = response2.data["search_metadata"]["performance"]["search_id"]
        
        # Search IDs should be different (unless cached)
        if not response2.data["search_metadata"]["performance"]["cached"]:
            self.assertNotEqual(search_id1, search_id2)

    def test_performance_timing_accuracy(self):
        """Test that performance timing is reasonable."""
        data = {"locations": [{"state": "CA"}]}
        
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        processing_time = response.data["search_metadata"]["performance"]["processing_time_ms"]
        
        # Processing time should be reasonable (under 1 second for small dataset)
        self.assertLess(processing_time, 1000)
        self.assertGreater(processing_time, 0)

    def test_cache_invalidation_with_different_requests(self):
        """Test that different requests don't interfere with each other's cache."""
        data1 = {"locations": [{"state": "CA"}]}
        data2 = {"locations": [{"state": "NY"}]}
        
        # Make requests with different data
        response1a = self.client.post(self.search_url, data1, format='json')
        response2a = self.client.post(self.search_url, data2, format='json')
        
        # Make same requests again
        response1b = self.client.post(self.search_url, data1, format='json')
        response2b = self.client.post(self.search_url, data2, format='json')
        
        # Both second requests should be cached
        self.assertEqual(
            response1b.data["search_metadata"]["performance"]["cached"], True
        )
        self.assertEqual(
            response2b.data["search_metadata"]["performance"]["cached"], True
        )
        
        # But results should be different
        self.assertNotEqual(response1b.data["results"], response2b.data["results"])

    def test_production_response_structure(self):
        """Test that production response includes all expected fields."""
        data = {"locations": [{"state": "CA"}], "text": "test"}
        
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check main structure
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        
        metadata = response.data["search_metadata"]
        
        # Check all production metadata fields
        expected_fields = [
            "total_count", "total_found", "radius_used", "radius_expanded",
            "filters_applied", "search_locations", "performance"
        ]
        
        for field in expected_fields:
            self.assertIn(field, metadata, f"Missing field: {field}")
        
        # Check performance metadata
        performance = metadata["performance"]
        expected_performance_fields = ["processing_time_ms", "search_id", "cached"]
        
        for field in expected_performance_fields:
            self.assertIn(field, performance, f"Missing performance field: {field}")

    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        # Create more businesses for performance testing
        additional_businesses = []
        for i in range(100, 200):  # Add 100 more businesses
            business = Business.objects.create(
                name=f"Performance Test Business {i}",
                city=f"Performance City {i}",
                state="TX",
                latitude=Decimal("30.2672"),
                longitude=Decimal("-97.7431")
            )
            additional_businesses.append(business)
        
        try:
            data = {"locations": [{"state": "TX"}]}
            
            response = self.client.post(self.search_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            metadata = response.data["search_metadata"]
            processing_time = metadata["performance"]["processing_time_ms"]
            
            # Even with larger dataset, should complete reasonably quickly
            self.assertLess(processing_time, 2000)  # Under 2 seconds
            
            # Should return results
            self.assertGreater(len(response.data["results"]), 0)
            
        finally:
            # Clean up additional businesses
            for business in additional_businesses:
                business.delete()
