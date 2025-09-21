"""Integration tests for API input validation.

Test HTTP request validation, error responses, and method handling.
"""
from rest_framework.test import APITestCase
from rest_framework import status


class BusinessSearchAPIValidationTest(APITestCase):
    """Test API-level input validation."""

    def test_invalid_json(self):
        """Test API response for invalid JSON."""
        response = self.client.post(
            '/businesses/search/',
            data='{"invalid": json}',  # Invalid JSON
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_locations(self):
        """Test API response for missing locations field."""
        response = self.client.post(
            '/businesses/search/',
            data={"text": "coffee"},  # Missing locations
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("locations", response.data["details"])

    def test_empty_locations(self):
        """Test API response for empty locations array."""
        response = self.client.post(
            '/businesses/search/',
            data={"locations": []},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("At least one location filter is required", str(response.data))

    def test_invalid_state_code(self):
        """Test API response for invalid state code."""
        response = self.client.post(
            '/businesses/search/',
            data={"locations": [{"state": "ZZ"}]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid state code", str(response.data))

    def test_missing_coordinates(self):
        """Test API response for incomplete coordinates."""
        response = self.client.post(
            '/businesses/search/',
            data={"locations": [{"lat": 34.052235}]},  # Missing lng
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_method_not_allowed(self):
        """Test that GET method returns 405 Method Not Allowed."""
        response = self.client.get('/businesses/search/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
