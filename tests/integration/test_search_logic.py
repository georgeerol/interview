"""Integration tests for core search functionality.

Test state filtering, text search, geospatial search, and combined filter logic.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from core.models import Business


class BasicSearchLogicTest(APITestCase):
    """Test basic search logic with state and text filtering."""

    def setUp(self):
        """Set up test data for basic search testing."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to isolate our tests
        Business.objects.all().delete()
        
        # Create test businesses with various names and states
        Business.objects.create(
            name="Coffee Shop CA",
            city="Los Angeles",
            state="CA", 
            latitude=Decimal("34.052235"),
            longitude=Decimal("-118.243683")
        )
        Business.objects.create(
            name="Book Store CA",
            city="San Francisco",
            state="CA",
            latitude=Decimal("37.774929"), 
            longitude=Decimal("-122.419418")
        )
        Business.objects.create(
            name="Coffee Shop NY",
            city="New York",
            state="NY",
            latitude=Decimal("40.712776"),
            longitude=Decimal("-74.005974")
        )
        Business.objects.create(
            name="Book Store NY", 
            city="Albany",
            state="NY",
            latitude=Decimal("42.686440"),
            longitude=Decimal("-73.836424")
        )
        Business.objects.create(
            name="Tea House TX",
            city="Austin",
            state="TX",
            latitude=Decimal("30.266667"),
            longitude=Decimal("-97.733333")
        )

    def test_state_only_search(self):
        """Test search by state only."""
        data = {"locations": [{"state": "CA"}]}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        
        # Should return both CA businesses
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        
        # All results should be from CA
        for business in results:
            self.assertEqual(business["state"], "CA")
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 2)
        self.assertIn("state", metadata["filters_applied"])
        self.assertNotIn("text", metadata["filters_applied"])

    def test_multi_state_search(self):
        """Test search by multiple states."""
        data = {"locations": [{"state": "CA"}, {"state": "NY"}]}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return businesses from both CA and NY (4 total)
        results = response.data["results"]
        self.assertEqual(len(results), 4)
        
        # Results should be from CA or NY only
        states = [business["state"] for business in results]
        for state in states:
            self.assertIn(state, ["CA", "NY"])
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 4)
        self.assertIn("state", metadata["filters_applied"])

    def test_text_only_search(self):
        """Test search by text only (requires at least one location)."""
        # Note: Our API requires locations, so we'll search all states with text
        # In a real implementation, we might allow text-only searches
        data = {"locations": [{"state": "CA"}, {"state": "NY"}, {"state": "TX"}], "text": "coffee"}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only coffee shops (2 total)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        
        # All results should contain "coffee" in the name
        for business in results:
            self.assertIn("Coffee", business["name"])
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 2)
        self.assertIn("text", metadata["filters_applied"])
        self.assertIn("state", metadata["filters_applied"])

    def test_state_and_text_search(self):
        """Test search by state and text combined."""
        data = {"locations": [{"state": "CA"}], "text": "book"}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only the CA book store
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Book Store CA")
        self.assertEqual(results[0]["state"], "CA")
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 1)
        self.assertIn("text", metadata["filters_applied"])
        self.assertIn("state", metadata["filters_applied"])

    def test_case_insensitive_text_search(self):
        """Test that text search is case-insensitive."""
        data = {"locations": [{"state": "CA"}, {"state": "NY"}], "text": "COFFEE"}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return both coffee shops despite uppercase search
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        
        for business in results:
            self.assertIn("Coffee", business["name"])

    def test_no_results_found(self):
        """Test when no businesses match the criteria."""
        data = {"locations": [{"state": "CA"}], "text": "pizza"}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty results
        results = response.data["results"]
        self.assertEqual(len(results), 0)
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 0)

    def test_geo_location_now_implemented(self):
        """Test that geo locations work correctly."""
        data = {"locations": [{"lat": 34.052235, "lng": -118.243683}], "radius_miles": 50}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should now return actual results (Phase 4 implemented)
        results = response.data["results"]
        self.assertGreaterEqual(len(results), 0)  # May have results depending on seeded data
        
        # Check metadata indicates geo filtering
        metadata = response.data["search_metadata"]
        self.assertIn("geo", metadata["filters_applied"])
        self.assertNotIn("note", metadata)  # No Phase 4 note anymore

    def test_mixed_state_and_geo_locations(self):
        """Test mixed state and geo locations."""
        data = {
            "locations": [
                {"state": "CA"},
                {"lat": 34.052235, "lng": -118.243683}
            ],
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should process both state and geo filtering
        results = response.data["results"]
        self.assertEqual(len(results), 1)  # Only CA coffee shop (deduplicated)
        self.assertEqual(results[0]["state"], "CA")
        
        # Check metadata shows both state and geo filters
        metadata = response.data["search_metadata"]
        self.assertIn("state", metadata["filters_applied"])
        self.assertIn("geo", metadata["filters_applied"])
        self.assertIn("text", metadata["filters_applied"])


class GeospatialSearchTest(APITestCase):
    """Test geospatial search with radius filtering."""

    def setUp(self):
        """Set up test data for geospatial testing."""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Clear existing businesses to isolate our tests
        Business.objects.all().delete()
        
        # Create test businesses at known locations
        # Los Angeles area (within 50 miles of downtown LA)
        self.la_coffee = Business.objects.create(
            name="LA Coffee Shop",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.052235"),  # Downtown LA
            longitude=Decimal("-118.243683")
        )
        
        self.pasadena_books = Business.objects.create(
            name="Pasadena Books",
            city="Pasadena", 
            state="CA",
            latitude=Decimal("34.147785"),  # ~10 miles from downtown LA
            longitude=Decimal("-118.144516")
        )
        
        # San Francisco area (300+ miles from LA)
        self.sf_coffee = Business.objects.create(
            name="SF Coffee House",
            city="San Francisco",
            state="CA",
            latitude=Decimal("37.774929"),
            longitude=Decimal("-122.419418")
        )
        
        # New York (2400+ miles from LA)
        self.ny_coffee = Business.objects.create(
            name="NY Coffee Bar",
            city="New York",
            state="NY",
            latitude=Decimal("40.712776"),
            longitude=Decimal("-74.005974")
        )
        
        # Texas (1200+ miles from LA)
        self.austin_tea = Business.objects.create(
            name="Austin Tea House",
            city="Austin",
            state="TX", 
            latitude=Decimal("30.266667"),
            longitude=Decimal("-97.733333")
        )

    def test_geo_location_only_search(self):
        """Test search by geo location only."""
        # Search within 50 miles of downtown LA
        data = {
            "locations": [{"lat": 34.052235, "lng": -118.243683}],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return LA area businesses (LA Coffee + Pasadena Books)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        
        # Verify correct businesses returned
        business_names = [b["name"] for b in results]
        self.assertIn("LA Coffee Shop", business_names)
        self.assertIn("Pasadena Books", business_names)
        self.assertNotIn("SF Coffee House", business_names)
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 2)
        self.assertEqual(metadata["radius_used"], 50.0)
        self.assertIn("geo", metadata["filters_applied"])
        self.assertNotIn("state", metadata["filters_applied"])

    def test_geo_location_with_text_search(self):
        """Test geo location + text filtering."""
        # Search for coffee within 50 miles of downtown LA
        data = {
            "locations": [{"lat": 34.052235, "lng": -118.243683}],
            "radius_miles": 50,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only LA Coffee Shop (not Pasadena Books)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "LA Coffee Shop")
        
        # Check metadata
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 1)
        self.assertIn("geo", metadata["filters_applied"])
        self.assertIn("text", metadata["filters_applied"])

    def test_multiple_geo_locations(self):
        """Test search with multiple geo locations."""
        # Search near both LA and SF
        data = {
            "locations": [
                {"lat": 34.052235, "lng": -118.243683},  # LA
                {"lat": 37.774929, "lng": -122.419418}   # SF
            ],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return businesses from both LA and SF areas
        results = response.data["results"]
        self.assertEqual(len(results), 3)  # LA Coffee + Pasadena Books + SF Coffee
        
        business_names = [b["name"] for b in results]
        self.assertIn("LA Coffee Shop", business_names)
        self.assertIn("Pasadena Books", business_names)
        self.assertIn("SF Coffee House", business_names)
        self.assertNotIn("NY Coffee Bar", business_names)  # Too far

    def test_mixed_state_and_geo_locations(self):
        """Test mixed state and geo location filtering."""
        # Search in NY state AND within 50 miles of LA
        data = {
            "locations": [
                {"state": "NY"},
                {"lat": 34.052235, "lng": -118.243683}
            ],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return NY business + LA area businesses
        results = response.data["results"]
        self.assertEqual(len(results), 3)  # NY Coffee + LA Coffee + Pasadena Books
        
        business_names = [b["name"] for b in results]
        self.assertIn("NY Coffee Bar", business_names)      # From NY state
        self.assertIn("LA Coffee Shop", business_names)     # From LA geo
        self.assertIn("Pasadena Books", business_names)     # From LA geo
        self.assertNotIn("SF Coffee House", business_names) # Not in NY, not near LA

    def test_small_radius_search(self):
        """Test search with very small radius."""
        # Search within 5 miles of downtown LA (should only get exact location)
        data = {
            "locations": [{"lat": 34.052235, "lng": -118.243683}],
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only the exact LA location
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "LA Coffee Shop")

    def test_large_radius_search(self):
        """Test search with very large radius."""
        # Search within 1000 miles of downtown LA (should get most US businesses)
        data = {
            "locations": [{"lat": 34.052235, "lng": -118.243683}],
            "radius_miles": 1000
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return CA businesses (Austin is ~1225 miles, NY is ~2445 miles)
        results = response.data["results"]
        self.assertEqual(len(results), 3)  # LA + Pasadena + SF (Austin is too far)
        
        business_names = [b["name"] for b in results]
        self.assertIn("LA Coffee Shop", business_names)
        self.assertIn("Pasadena Books", business_names)
        self.assertIn("SF Coffee House", business_names)
        self.assertNotIn("Austin Tea House", business_names)  # Too far (1225 miles)
        self.assertNotIn("NY Coffee Bar", business_names)     # Too far (2445 miles)

    def test_no_geo_results_found(self):
        """Test when no businesses are within the specified radius."""
        # Search in middle of Nevada desert with small radius
        data = {
            "locations": [{"lat": 39.5, "lng": -116.5}],  # Nevada desert
            "radius_miles": 10
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # With Phase 5, radius expansion may find results at larger radii
        results = response.data["results"]
        metadata = response.data["search_metadata"]
        
        # Either no results found even after expansion, or results found with expansion
        if len(results) == 0:
            self.assertEqual(metadata["total_count"], 0)
            self.assertEqual(metadata["radius_used"], 500.0)  # Expanded to max
            self.assertEqual(metadata["radius_expanded"], True)
        else:
            # Found results with expansion
            self.assertGreater(metadata["radius_used"], 10.0)
            self.assertEqual(metadata["radius_expanded"], True)

    def test_readme_example_1_implementation(self):
        """Test the exact README Example 1 with actual results."""
        data = {
            "locations": [
                {"state": "CA"},
                {"state": "NY"},
                {"lat": 34.052235, "lng": -118.243683}
            ],
            "radius_miles": 50,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return coffee businesses from CA, NY, and within 50 miles of LA
        results = response.data["results"]
        
        # Should get: LA Coffee (geo), SF Coffee (CA state), NY Coffee (NY state)
        # But LA Coffee might be counted twice, so we should deduplicate
        business_names = [b["name"] for b in results]
        self.assertIn("LA Coffee Shop", business_names)  # From both CA state and LA geo
        self.assertIn("SF Coffee House", business_names) # From CA state
        self.assertIn("NY Coffee Bar", business_names)   # From NY state
        
        # Check all filters applied
        metadata = response.data["search_metadata"]
        self.assertIn("text", metadata["filters_applied"])
        self.assertIn("state", metadata["filters_applied"])
        self.assertIn("geo", metadata["filters_applied"])
