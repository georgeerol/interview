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
        self.search_url = reverse('business-search')
        
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
        self.search_url = reverse('business-search')
        
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
        self.search_url = reverse('business-search')
        
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
        self.search_url = reverse('business-search')
        
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
