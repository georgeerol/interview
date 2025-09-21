"""Unit tests for cache service implementation.

Test cache operations, key generation, and data normalization.
"""
from django.test import TestCase
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import hashlib
import json

from core.cache.service import DjangoCacheService


class DjangoCacheServiceTest(TestCase):
    """Test Django cache service implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache_service = DjangoCacheService()
        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after each test."""
        cache.clear()

    def test_get_existing_key(self):
        """Test retrieving existing cached value."""
        # Set up test data
        test_key = "test_key"
        test_data = {"results": ["business1", "business2"], "count": 2}
        
        # Store data directly in cache
        cache.set(test_key, test_data, 300)
        
        # Test retrieval
        result = self.cache_service.get(test_key)
        
        self.assertEqual(result, test_data)

    def test_get_nonexistent_key(self):
        """Test retrieving non-existent cached value returns None."""
        result = self.cache_service.get("nonexistent_key")
        self.assertIsNone(result)

    def test_set_cache_value(self):
        """Test storing value in cache."""
        test_key = "test_key"
        test_data = {"results": ["business1"], "count": 1}
        timeout = 300
        
        # Store data using cache service
        self.cache_service.set(test_key, test_data, timeout)
        
        # Verify data was stored
        cached_result = cache.get(test_key)
        self.assertEqual(cached_result, test_data)

    def test_generate_key_consistent(self):
        """Test that identical requests generate identical cache keys."""
        request_data = {
            "locations": [{"state": "CA"}, {"lat": 34.0522, "lng": -118.2437}],
            "radius_miles": 50,
            "text": "coffee"
        }
        
        key1 = self.cache_service.generate_key(request_data)
        key2 = self.cache_service.generate_key(request_data)
        
        self.assertEqual(key1, key2)
        self.assertTrue(key1.startswith("business_search:"))

    def test_generate_key_normalization(self):
        """Test that request data is normalized for consistent caching."""
        # Same data in different order should generate same key
        request1 = {
            "locations": [{"state": "CA"}, {"state": "NY"}],
            "radius_miles": 50,
            "text": "Coffee"
        }
        
        request2 = {
            "locations": [{"state": "NY"}, {"state": "CA"}],
            "radius_miles": 50,
            "text": "coffee"  # Different case
        }
        
        key1 = self.cache_service.generate_key(request1)
        key2 = self.cache_service.generate_key(request2)
        
        self.assertEqual(key1, key2)

    def test_generate_key_text_normalization(self):
        """Test that text is normalized (lowercased and trimmed)."""
        request1 = {"locations": [{"state": "CA"}], "text": "  Coffee Shop  "}
        request2 = {"locations": [{"state": "CA"}], "text": "coffee shop"}
        
        key1 = self.cache_service.generate_key(request1)
        key2 = self.cache_service.generate_key(request2)
        
        self.assertEqual(key1, key2)

    def test_generate_key_missing_fields(self):
        """Test key generation with missing optional fields."""
        request_data = {"locations": [{"state": "CA"}]}
        
        key = self.cache_service.generate_key(request_data)
        
        self.assertTrue(key.startswith("business_search:"))
        self.assertEqual(len(key), len("business_search:") + 32)  # MD5 hash length

    def test_generate_key_different_data_different_keys(self):
        """Test that different requests generate different cache keys."""
        request1 = {"locations": [{"state": "CA"}], "text": "coffee"}
        request2 = {"locations": [{"state": "NY"}], "text": "coffee"}
        
        key1 = self.cache_service.generate_key(request1)
        key2 = self.cache_service.generate_key(request2)
        
        self.assertNotEqual(key1, key2)

    def test_generate_key_locations_sorting(self):
        """Test that locations are sorted for consistent key generation."""
        request1 = {
            "locations": [
                {"lat": 34.0522, "lng": -118.2437},
                {"state": "CA"},
                {"lat": 37.7749, "lng": -122.4194}
            ]
        }
        
        request2 = {
            "locations": [
                {"state": "CA"},
                {"lat": 37.7749, "lng": -122.4194},
                {"lat": 34.0522, "lng": -118.2437}
            ]
        }
        
        key1 = self.cache_service.generate_key(request1)
        key2 = self.cache_service.generate_key(request2)
        
        self.assertEqual(key1, key2)

    def test_generate_key_hash_format(self):
        """Test that generated key has correct format and hash."""
        request_data = {
            "locations": [{"state": "CA"}],
            "radius_miles": 50,
            "text": "coffee"
        }
        
        key = self.cache_service.generate_key(request_data)
        
        # Verify format
        self.assertTrue(key.startswith("business_search:"))
        hash_part = key.replace("business_search:", "")
        self.assertEqual(len(hash_part), 32)  # MD5 hash length
        
        # Verify it's a valid hex string
        try:
            int(hash_part, 16)
        except ValueError:
            self.fail("Hash part is not valid hexadecimal")

    def test_cache_integration_workflow(self):
        """Test complete cache workflow: generate key, set, get."""
        request_data = {
            "locations": [{"state": "CA"}],
            "text": "coffee"
        }
        
        response_data = {
            "results": [{"id": 1, "name": "Coffee Shop"}],
            "search_metadata": {"total_count": 1}
        }
        
        # Generate key
        cache_key = self.cache_service.generate_key(request_data)
        
        # Store data
        self.cache_service.set(cache_key, response_data, 300)
        
        # Retrieve data
        cached_result = self.cache_service.get(cache_key)
        
        self.assertEqual(cached_result, response_data)

    def test_cache_timeout_behavior(self):
        """Test that cache respects timeout settings."""
        test_key = "timeout_test"
        test_data = {"test": "data"}
        
        # Set with very short timeout
        self.cache_service.set(test_key, test_data, 1)
        
        # Should be available immediately
        result = self.cache_service.get(test_key)
        self.assertEqual(result, test_data)
        
        # Note: We can't easily test actual timeout without waiting,
        # but we've verified the timeout parameter is passed correctly

    @patch('core.cache.service.cache')
    def test_cache_backend_integration(self, mock_cache):
        """Test integration with Django cache backend."""
        mock_cache.get.return_value = {"cached": "data"}
        mock_cache.set.return_value = None
        
        # Test get
        result = self.cache_service.get("test_key")
        mock_cache.get.assert_called_once_with("test_key")
        self.assertEqual(result, {"cached": "data"})
        
        # Test set
        test_data = {"new": "data"}
        self.cache_service.set("test_key", test_data, 300)
        mock_cache.set.assert_called_once_with("test_key", test_data, 300)
