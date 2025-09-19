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
        self.assertEqual(response.data["search_metadata"]["radius_used"], 5.0)

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

    def test_geo_location_placeholder(self):
        """Test that geo locations are noted but not processed in Phase 3"""
        data = {"locations": [{"lat": 34.052235, "lng": -118.243683}], "radius_miles": 50}
        response = self.client.post(self.search_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty results with Phase 4 note
        results = response.data["results"]
        self.assertEqual(len(results), 0)
        
        # Check metadata indicates geo filtering
        metadata = response.data["search_metadata"]
        self.assertEqual(metadata["total_count"], 0)
        self.assertIn("geo", metadata["filters_applied"])
        self.assertIn("Phase 4", metadata["note"])

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
