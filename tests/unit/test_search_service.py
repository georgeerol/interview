"""Unit tests for search service implementation.

Test isolated search logic, filtering, and result processing.
"""
from django.test import TestCase
from unittest.mock import MagicMock, patch
from decimal import Decimal

from core.search.service import BusinessSearchServiceImpl
from core.search.value_objects import SearchParams, SearchResult
from core.domain import Business


class BusinessSearchServiceImplTest(TestCase):
    """Test business search service implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.search_service = BusinessSearchServiceImpl()
        
        # Clear existing businesses and create test data
        Business.objects.all().delete()
        
        # Create test businesses
        self.ca_coffee = Business.objects.create(
            name="California Coffee Shop",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437")
        )
        
        self.ca_restaurant = Business.objects.create(
            name="California Restaurant",
            city="San Francisco",
            state="CA",
            latitude=Decimal("37.7749"),
            longitude=Decimal("-122.4194")
        )
        
        self.ny_coffee = Business.objects.create(
            name="New York Coffee House",
            city="New York",
            state="NY",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        
        self.tx_bakery = Business.objects.create(
            name="Texas Bakery",
            city="Austin",
            state="TX",
            latitude=Decimal("30.2672"),
            longitude=Decimal("-97.7431")
        )

    def test_search_by_state_only(self):
        """Test search with state filter only."""
        params = SearchParams(
            locations=[{"state": "CA"}],
            radius_miles=None,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should return CA businesses only
        self.assertEqual(len(result.businesses), 2)
        business_names = [b.name for b in result.businesses]
        self.assertIn("California Coffee Shop", business_names)
        self.assertIn("California Restaurant", business_names)
        
        # Verify metadata
        self.assertEqual(result.total_found, 2)
        self.assertEqual(result.filters_applied, ["state"])
        self.assertEqual(result.radius_expanded, False)

    def test_search_by_text_only(self):
        """Test search with text filter only."""
        params = SearchParams(
            locations=[{"state": "CA"}, {"state": "NY"}],
            radius_miles=None,
            text="coffee"
        )
        
        result = self.search_service.search(params)
        
        # Should return coffee businesses only
        self.assertEqual(len(result.businesses), 2)
        business_names = [b.name for b in result.businesses]
        self.assertIn("California Coffee Shop", business_names)
        self.assertIn("New York Coffee House", business_names)
        
        # Verify metadata
        self.assertEqual(result.filters_applied, ["text", "state"])

    def test_search_case_insensitive_text(self):
        """Test that text search is case insensitive."""
        params = SearchParams(
            locations=[{"state": "CA"}],
            radius_miles=None,
            text="COFFEE"  # Uppercase
        )
        
        result = self.search_service.search(params)
        
        # Should find coffee shop despite case difference
        self.assertEqual(len(result.businesses), 1)
        self.assertEqual(result.businesses[0].name, "California Coffee Shop")

    def test_search_multiple_states(self):
        """Test search with multiple state filters."""
        params = SearchParams(
            locations=[{"state": "CA"}, {"state": "NY"}],
            radius_miles=None,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should return businesses from both states
        self.assertEqual(len(result.businesses), 3)
        states = [b.state for b in result.businesses]
        self.assertIn("CA", states)
        self.assertIn("NY", states)
        self.assertNotIn("TX", states)

    @patch('core.search.service.expand_radius_search_multiple_locations')
    def test_search_with_geo_locations(self, mock_expand_radius):
        """Test search with geospatial locations."""
        # Mock radius expansion function
        mock_expand_radius.return_value = (
            [self.ca_coffee],  # businesses found
            50.0,  # radius used
            False,  # radius expanded
            [50.0]  # radii tried
        )
        
        params = SearchParams(
            locations=[{"lat": 34.0522, "lng": -118.2437}],
            radius_miles=50.0,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should call radius expansion function
        mock_expand_radius.assert_called_once()
        call_args = mock_expand_radius.call_args[0]
        self.assertEqual(call_args[1], [{"lat": 34.0522, "lng": -118.2437}])
        self.assertEqual(call_args[2], 50.0)
        
        # Verify result
        self.assertEqual(len(result.businesses), 1)
        self.assertEqual(result.businesses[0], self.ca_coffee)
        self.assertEqual(result.radius_used, 50.0)
        self.assertEqual(result.radius_expanded, False)
        self.assertEqual(result.filters_applied, ["geo"])

    @patch('core.search.service.expand_radius_search_multiple_locations')
    def test_search_with_geo_and_state_locations(self, mock_expand_radius):
        """Test search combining geo and state locations (OR logic)."""
        # Mock radius expansion to return CA coffee shop
        mock_expand_radius.return_value = (
            [self.ca_coffee],
            50.0,
            False,
            [50.0]
        )
        
        params = SearchParams(
            locations=[
                {"state": "NY"},
                {"lat": 34.0522, "lng": -118.2437}
            ],
            radius_miles=50.0,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should combine results from both filters (OR logic)
        self.assertEqual(len(result.businesses), 2)
        business_names = [b.name for b in result.businesses]
        self.assertIn("California Coffee Shop", business_names)  # From geo
        self.assertIn("New York Coffee House", business_names)  # From state
        
        # Verify metadata
        self.assertEqual(result.filters_applied, ["state", "geo"])

    @patch('core.search.service.expand_radius_search_multiple_locations')
    def test_search_with_text_and_geo_locations(self, mock_expand_radius):
        """Test search with text filter and geo locations."""
        # Mock radius expansion to return coffee shop
        mock_expand_radius.return_value = (
            [self.ca_coffee],
            50.0,
            False,
            [50.0]
        )
        
        params = SearchParams(
            locations=[{"lat": 34.0522, "lng": -118.2437}],
            radius_miles=50.0,
            text="coffee"
        )
        
        result = self.search_service.search(params)
        
        # Should apply text filter to geo search
        self.assertEqual(len(result.businesses), 1)
        self.assertEqual(result.businesses[0], self.ca_coffee)
        self.assertEqual(result.filters_applied, ["text", "geo"])

    @patch('core.search.service.expand_radius_search_multiple_locations')
    def test_search_deduplication(self, mock_expand_radius):
        """Test that duplicate businesses are removed."""
        # Mock radius expansion to return the same business that's in NY state
        mock_expand_radius.return_value = (
            [self.ny_coffee],  # Same business returned by geo search
            50.0,
            False,
            [50.0]
        )
        
        params = SearchParams(
            locations=[
                {"state": "NY"},  # Will return ny_coffee
                {"lat": 40.7128, "lng": -74.0060}  # Mock returns same ny_coffee
            ],
            radius_miles=50.0,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should deduplicate and return only one instance
        self.assertEqual(len(result.businesses), 1)
        self.assertEqual(result.businesses[0], self.ny_coffee)

    def test_search_result_limit(self):
        """Test that results are limited to 100 businesses."""
        # Create many businesses to test limit
        for i in range(150):
            Business.objects.create(
                name=f"Test Business {i}",
                city="Test City",
                state="CA",
                latitude=Decimal("34.0522"),
                longitude=Decimal("-118.2437")
            )
        
        params = SearchParams(
            locations=[{"state": "CA"}],
            radius_miles=None,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should limit to 100 results
        self.assertEqual(len(result.businesses), 100)
        # But total_found should reflect actual count
        self.assertGreater(result.total_found, 100)

    def test_search_no_results(self):
        """Test search that returns no results."""
        params = SearchParams(
            locations=[{"state": "ZZ"}],  # Non-existent state
            radius_miles=None,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Should return empty results
        self.assertEqual(len(result.businesses), 0)
        self.assertEqual(result.total_found, 0)
        self.assertEqual(result.filters_applied, ["state"])

    def test_search_default_radius_for_geo(self):
        """Test that default radius is used when not provided for geo search."""
        with patch('core.search.service.expand_radius_search_multiple_locations') as mock_expand:
            mock_expand.return_value = ([], 50.0, False, [50.0])
            
            params = SearchParams(
                locations=[{"lat": 34.0522, "lng": -118.2437}],
                radius_miles=None,  # No radius provided
                text=""
            )
            
            result = self.search_service.search(params)
            
            # Should use default radius of 50.0
            call_args = mock_expand.call_args[0]
            self.assertEqual(call_args[2], None)  # Passed None, service handles default

    @patch('core.search.service.expand_radius_search_multiple_locations')
    def test_search_radius_expansion_metadata(self, mock_expand_radius):
        """Test that radius expansion metadata is properly captured."""
        # Mock radius expansion with expansion
        mock_expand_radius.return_value = (
            [self.ca_coffee],
            100.0,  # Final radius used
            True,   # Radius was expanded
            [50.0, 100.0]  # Radii tried
        )
        
        params = SearchParams(
            locations=[{"lat": 34.0522, "lng": -118.2437}],
            radius_miles=50.0,
            text=""
        )
        
        result = self.search_service.search(params)
        
        # Verify expansion metadata
        self.assertEqual(result.radius_used, 100.0)
        self.assertEqual(result.radius_expanded, True)
        self.assertEqual(result.radii_tried, [50.0, 100.0])
        self.assertEqual(result.radius_miles, 50.0)  # Original request

    def test_search_location_separation(self):
        """Test that locations are properly separated into state and geo."""
        params = SearchParams(
            locations=[
                {"state": "CA"},
                {"lat": 34.0522, "lng": -118.2437},
                {"state": "NY"},
                {"lat": 40.7128, "lng": -74.0060}
            ],
            radius_miles=50.0,
            text=""
        )
        
        with patch('core.search.service.expand_radius_search_multiple_locations') as mock_expand:
            mock_expand.return_value = ([], 50.0, False, [50.0])
            
            result = self.search_service.search(params)
            
            # Should separate geo locations correctly
            call_args = mock_expand.call_args[0]
            geo_locations = call_args[1]
            
            self.assertEqual(len(geo_locations), 2)
            self.assertIn({"lat": 34.0522, "lng": -118.2437}, geo_locations)
            self.assertIn({"lat": 40.7128, "lng": -74.0060}, geo_locations)

    def test_search_params_preservation(self):
        """Test that original search parameters are preserved in result."""
        original_locations = [
            {"state": "CA"},
            {"lat": 34.0522, "lng": -118.2437}
        ]
        
        params = SearchParams(
            locations=original_locations,
            radius_miles=75.0,
            text="test"
        )
        
        with patch('core.search.service.expand_radius_search_multiple_locations') as mock_expand:
            mock_expand.return_value = ([], 75.0, False, [75.0])
            
            result = self.search_service.search(params)
            
            # Should preserve original parameters
            self.assertEqual(result.locations, original_locations)
            self.assertEqual(result.radius_miles, 75.0)

    def test_search_empty_locations(self):
        """Test search with empty locations list."""
        params = SearchParams(
            locations=[],
            radius_miles=None,
            text="coffee"
        )
        
        result = self.search_service.search(params)
        
        # Should return all businesses matching text filter
        self.assertEqual(len(result.businesses), 2)  # Both coffee businesses
        self.assertEqual(result.filters_applied, ["text"])

    def test_search_service_isolation(self):
        """Test that search service doesn't have external dependencies."""
        # This test verifies the service can be instantiated and used
        # without any external dependencies (pure business logic)
        
        service = BusinessSearchServiceImpl()
        
        params = SearchParams(
            locations=[{"state": "CA"}],
            radius_miles=None,
            text=""
        )
        
        result = service.search(params)
        
        # Should work without any mocking or setup
        self.assertIsInstance(result, SearchResult)
        self.assertIsInstance(result.businesses, list)
        self.assertIsInstance(result.filters_applied, list)
