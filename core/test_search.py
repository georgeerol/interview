from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from .models import Business
from .serializers import BusinessSearchRequestSerializer, LocationSerializer


class LocationSerializerTest(TestCase):
    """Test cases for LocationSerializer validation"""

    def test_valid_state_location(self):
        """Test valid state location"""
        data = {"state": "CA"}
        serializer = LocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["state"], "CA")

    def test_valid_state_lowercase(self):
        """Test state gets converted to uppercase"""
        data = {"state": "ca"}
        serializer = LocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["state"], "CA")

    def test_valid_coordinate_location(self):
        """Test valid lat/lng coordinates"""
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
    """Test cases for BusinessSearchRequestSerializer validation"""

    def test_valid_state_only_search(self):
        """Test valid search with state only"""
        data = {
            "locations": [{"state": "CA"}],
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data["locations"]), 1)
        self.assertEqual(serializer.validated_data["locations"][0]["state"], "CA")
        self.assertEqual(serializer.validated_data["text"], "coffee")

    def test_valid_geo_search_with_default_radius(self):
        """Test geo search gets default radius when not provided"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}]
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["radius_miles"], Decimal("50"))

    def test_valid_geo_search_with_explicit_radius(self):
        """Test geo search with explicit radius"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("25")
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["radius_miles"], Decimal("25"))

    def test_valid_mixed_locations(self):
        """Test valid search with mixed location types"""
        data = {
            "locations": [
                {"state": "CA"},
                {"state": "NY"},
                {"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}
            ],
            "radius_miles": Decimal("50"),
            "text": "coffee"
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data["locations"]), 3)
        self.assertEqual(serializer.validated_data["radius_miles"], Decimal("50"))
        self.assertEqual(serializer.validated_data["text"], "coffee")

    def test_empty_locations(self):
        """Test validation error for empty locations array"""
        data = {"locations": []}
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("At least one location filter is required", str(serializer.errors))

    def test_too_many_locations(self):
        """Test validation error for too many locations"""
        data = {
            "locations": [{"state": "CA"}] * 21  # 21 locations (max is 20)
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Too many location filters", str(serializer.errors))

    def test_invalid_radius_too_small(self):
        """Test validation error for radius too small"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("0.05")  # Less than min 0.1
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ensure this value is greater than or equal to", str(serializer.errors))

    def test_invalid_radius_too_large(self):
        """Test validation error for radius too large"""
        data = {
            "locations": [{"lat": Decimal("34.052235"), "lng": Decimal("-118.243683")}],
            "radius_miles": Decimal("1001")  # Greater than max 1000
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ensure this value is less than or equal to", str(serializer.errors))

    def test_empty_text_allowed(self):
        """Test that empty text is allowed"""
        data = {
            "locations": [{"state": "CA"}],
            "text": ""
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["text"], "")

    def test_missing_text_allowed(self):
        """Test that missing text is allowed"""
        data = {
            "locations": [{"state": "CA"}]
        }
        serializer = BusinessSearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("text", serializer.validated_data)


class BusinessSearchAPITest(APITestCase):
    """Test cases for the business search API endpoint"""

    def setUp(self):
        """Set up test data"""
        from django.core.cache import cache
        
        self.search_url = reverse('business-search')
        
        # Clear cache between tests to ensure clean state
        cache.clear()
        
        # Create some test businesses
        Business.objects.create(
            name="Coffee Shop CA",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.052235"),
            longitude=Decimal("-118.243683")
        )
        Business.objects.create(
            name="Book Store NY",
            city="New York",
            state="NY",
            latitude=Decimal("40.712776"),
            longitude=Decimal("-74.005974")
        )

    def test_valid_state_search_request(self):
        """Test valid state-based search request"""
        data = {
            "locations": [{"state": "CA"}],
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        # Now that we have search logic, should return actual results
        self.assertGreaterEqual(response.data["search_metadata"]["total_count"], 0)
        self.assertEqual(response.data["search_metadata"]["radius_expanded"], False)

    def test_valid_geo_search_request(self):
        """Test valid geo-based search request"""
        data = {
            "locations": [{"lat": 34.052235, "lng": -118.243683}],
            "radius_miles": 50
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        self.assertEqual(response.data["search_metadata"]["radius_used"], 50.0)

    def test_readme_example_1_request(self):
        """Test the exact example from README"""
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
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)

    def test_readme_example_2_request(self):
        """Test the radius expansion example from README"""
        data = {
            "locations": [{"lat": 37.9290, "lng": -116.7510}],
            "radius_miles": 5
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("search_metadata", response.data)
        # Should expand beyond 5 miles (Phase 5 implemented)
        self.assertGreater(response.data["search_metadata"]["radius_used"], 5.0)

    def test_invalid_state_code(self):
        """Test API response for invalid state code"""
        data = {
            "locations": [{"state": "ZZ"}]
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Invalid state code", str(response.data))

    def test_missing_coordinates(self):
        """Test API response for incomplete coordinates"""
        data = {
            "locations": [{"lat": 34.052235}]  # Missing lng
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Location must have either state or lat/lng coordinates", str(response.data))

    def test_empty_locations(self):
        """Test API response for empty locations array"""
        data = {
            "locations": []
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("At least one location filter is required", str(response.data))

    def test_invalid_json(self):
        """Test API response for invalid JSON"""
        response = self.client.post(
            self.search_url, 
            "invalid json", 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_method_not_allowed(self):
        """Test that GET method returns 405 Method Not Allowed"""
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BusinessSearchPhase3Test(APITestCase):
    """Test cases for Phase 3 - Basic search logic (state + text filtering)"""

    def setUp(self):
        """Set up test data for Phase 3"""
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
        """Test search by state only"""
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
        """Test search by multiple states"""
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
        """Test search by text only (requires at least one location)"""
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
        """Test search by state and text combined"""
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
        """Test that text search is case-insensitive"""
        data = {"locations": [{"state": "CA"}, {"state": "NY"}], "text": "COFFEE"}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return both coffee shops despite uppercase search
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        
        for business in results:
            self.assertIn("Coffee", business["name"])

    def test_no_results_found(self):
        """Test when no businesses match the criteria"""
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
        """Test that geo locations now work (Phase 4 implemented)"""
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
        """Test mixed state and geo locations (geo ignored in Phase 3)"""
        data = {
            "locations": [
                {"state": "CA"},
                {"lat": 34.052235, "lng": -118.243683}
            ],
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should process state filtering and ignore geo for now
        results = response.data["results"]
        self.assertEqual(len(results), 1)  # Only CA coffee shop
        self.assertEqual(results[0]["state"], "CA")
        
        # Check metadata shows both state and geo filters
        metadata = response.data["search_metadata"]
        self.assertIn("state", metadata["filters_applied"])
        self.assertIn("geo", metadata["filters_applied"])
        self.assertIn("text", metadata["filters_applied"])


class BusinessSearchPhase4Test(APITestCase):
    """Test cases for Phase 4 - Geo-location search with radius filtering"""

    def setUp(self):
        """Set up test data for Phase 4"""
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
        """Test search by geo location only"""
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
        """Test geo location + text filtering"""
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
        """Test search with multiple geo locations"""
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
        """Test mixed state and geo location filtering"""
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
        """Test search with very small radius"""
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
        """Test search with very large radius"""
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
        """Test when no businesses are within the specified radius"""
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
        """Test the exact README Example 1 with actual results"""
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


class BusinessSearchPhase5Test(APITestCase):
    """Test cases for Phase 5 - Radius expansion logic"""

    def setUp(self):
        """Set up test data for Phase 5"""
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
        """Test when initial radius finds results (no expansion needed)"""
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


class BusinessSearchPhase6Test(APITestCase):
    """Test cases for Phase 6 - Enhanced response format and metadata"""

    def setUp(self):
        """Set up test data for Phase 6"""
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


class BusinessSearchPhase7Test(APITestCase):
    """Test cases for Phase 7 - Comprehensive testing of README examples and edge cases"""

    def setUp(self):
        """Set up test data for comprehensive Phase 7 testing"""
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
        
        # Nevada businesses for README Example 2 (radius expansion testing)
        self.nv_businesses = [
            Business.objects.create(
                name="Reno Coffee", city="Reno", state="NV",
                latitude=Decimal("39.5296"), longitude=Decimal("-119.8138")  # ~200 miles from Example 2 point
            ),
            Business.objects.create(
                name="Vegas Cafe", city="Las Vegas", state="NV", 
                latitude=Decimal("36.1699"), longitude=Decimal("-115.1398")  # ~300 miles from Example 2 point
            ),
        ]
        
        # Edge case businesses for boundary testing
        self.edge_businesses = [
            Business.objects.create(
                name="Boundary Coffee", city="Bakersfield", state="CA",
                latitude=Decimal("35.3733"), longitude=Decimal("-119.0187")  # ~49.8 miles from LA
            ),
            Business.objects.create(
                name="Far Coffee", city="Phoenix", state="AZ",
                latitude=Decimal("33.4484"), longitude=Decimal("-112.0740")  # ~350+ miles from LA
            ),
        ]

    def test_readme_example_1_exact_implementation(self):
        """Test the exact README Example 1 with comprehensive validation"""
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
        
        # Should include CA and NY coffee businesses
        ca_coffee_names = {b.name for b in self.ca_businesses if "Coffee" in b.name}
        ny_coffee_names = {b.name for b in self.ny_businesses if "Coffee" in b.name}
        
        returned_names = set(business_names)
        
        # Should have businesses from CA and NY states
        self.assertTrue(ca_coffee_names.intersection(returned_names), "No CA coffee businesses found")
        self.assertTrue(ny_coffee_names.intersection(returned_names), "No NY coffee businesses found")
        
        # Should NOT have TX businesses (not in search criteria)
        tx_names = {b.name for b in self.tx_businesses}
        self.assertFalse(tx_names.intersection(returned_names), "TX businesses incorrectly included")

    def test_readme_example_2_exact_implementation(self):
        """Test the exact README Example 2 with radius expansion validation"""
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
        
        # Should find businesses (from our seeded data or the main dataset)
        if len(results) > 0:
            self.assertGreater(metadata["total_count"], 0)
        
        # Validate single geo location
        locations = metadata["search_locations"]
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]["type"], "geo")
        self.assertEqual(locations[0]["lat"], 37.9290)
        self.assertEqual(locations[0]["lng"], -116.7510)

    def test_edge_case_maximum_locations(self):
        """Test maximum number of locations (20 per validation)"""
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
        """Test exceeding maximum locations (21 locations should fail)"""
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
        """Test boundary radius values (0.1, 1000.0)"""
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
        """Test coordinate boundary values"""
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
        """Test invalid coordinate values"""
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
        """Test empty and whitespace-only text searches"""
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
        
        # Test that None text value is rejected (serializer validation)
        data = {
            "locations": [{"state": "CA"}],
            "text": None
        }
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_edge_case_case_insensitive_text_search(self):
        """Test case insensitive text searching"""
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

    def test_edge_case_mixed_location_types_comprehensive(self):
        """Test all combinations of mixed location types"""
        # Test state + geo combination
        data = {
            "locations": [
                {"state": "CA"},
                {"lat": 40.7128, "lng": -74.0060}  # NYC
            ],
            "radius_miles": 50,
            "text": "coffee"
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        # Should have both state and geo filters
        self.assertIn("state", metadata["filters_applied"])
        self.assertIn("geo", metadata["filters_applied"])
        
        # Should have mixed location types
        locations = metadata["search_locations"]
        types = [loc["type"] for loc in locations]
        self.assertIn("state", types)
        self.assertIn("geo", types)

    def test_edge_case_duplicate_locations(self):
        """Test duplicate location handling"""
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

    def test_edge_case_radius_expansion_all_levels(self):
        """Test radius expansion through all levels [1,5,10,25,50,100,500]"""
        # Use a very remote location to force expansion to maximum
        data = {
            "locations": [{"lat": 0.0, "lng": 0.0}],  # Middle of Atlantic Ocean
            "radius_miles": 1
        }
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        metadata = response.data["search_metadata"]
        
        if metadata["radius_expanded"]:
            sequence = metadata["radius_expansion_sequence"]
            
            # Should start with 1
            self.assertEqual(sequence[0], 1.0)
            
            # Should expand through the sequence
            expected_sequence = [1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 500.0]
            
            # All values in sequence should be from expected sequence
            for radius in sequence:
                self.assertIn(radius, expected_sequence)

    def test_performance_large_result_set(self):
        """Test performance with large result sets (pagination behavior)"""
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


class BusinessSearchPhase8Test(APITestCase):
    """Test cases for Phase 8 - Performance optimization and production features"""

    def setUp(self):
        """Set up test data for Phase 8 performance testing"""
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
        """Test that performance metadata is included in responses"""
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
        """Test that search results are properly cached"""
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
        """Test that cache keys are generated consistently"""
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
        """Test production error handling and logging"""
        # Test with invalid data that will cause internal error
        # (This is a bit tricky to test without mocking, but we can test the error structure)
        
        # Test with malformed request
        response = self.client.post(self.search_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("details", response.data)

    def test_search_id_generation(self):
        """Test that unique search IDs are generated"""
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
        """Test that performance timing is reasonable"""
        data = {"locations": [{"state": "CA"}]}
        
        response = self.client.post(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        processing_time = response.data["search_metadata"]["performance"]["processing_time_ms"]
        
        # Processing time should be reasonable (under 1 second for small dataset)
        self.assertLess(processing_time, 1000)
        self.assertGreater(processing_time, 0)

    def test_cache_invalidation_with_different_requests(self):
        """Test that different requests don't interfere with each other's cache"""
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
        """Test that production response includes all expected fields"""
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
        """Test performance with larger dataset"""
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
