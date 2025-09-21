"""
Business Search API Views

SOLID-compliant view implementation with dependency injection.
Follows all SOLID principles for maintainable, testable code.
"""
from typing import Dict, Any

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from .models import Business
from .serializers import BusinessSerializer, BusinessSearchRequestSerializer
from .interfaces import SearchParams
from .container import get_container


class BusinessViewSet(viewsets.ModelViewSet):
	"""
	Business ViewSet following SOLID principles.
	
	Single Responsibility: Handle HTTP requests/responses only.
	Dependency Inversion: Depends on abstractions, not concretions.
	Open/Closed: Easy to extend without modification.
	Interface Segregation: Uses focused interfaces for each concern.
	Liskov Substitution: Can be substituted with any compatible implementation.
	"""
	queryset = Business.objects.all().order_by("name")
	serializer_class = BusinessSerializer
	permission_classes = [AllowAny]

	def __init__(self, *args, **kwargs):
		"""Initialize with dependency injection."""
		super().__init__(*args, **kwargs)
		# Dependency Inversion: Depend on abstractions, not concretions
		container = get_container()
		self.search_service = container.search_service
		self.cache_service = container.cache_service
		self.metrics_service = container.metrics_service
		self.response_builder = container.response_builder
		self.logger = container.logger

	@action(detail=False, methods=["post"], url_path="search")
	def search(self, request):
		"""
		Search businesses - SOLID compliant thin HTTP layer.
		
		Single Responsibility: Handle HTTP request/response only.
		All business logic delegated to services via dependency injection.
		
		Expected input:
		{
			"locations": [
				{"state": "CA"},
				{"lat": 34.052235, "lng": -118.243683}
			],
			"radius_miles": 50,
			"text": "coffee"
		}
		"""
		# Step 1: Start tracking (delegated to metrics service)
		search_id = self.metrics_service.start_tracking(request)
		
		try:
			# Step 2: Validate input (using existing serializer)
			serializer = BusinessSearchRequestSerializer(data=request.data)
			if not serializer.is_valid():
				return self.response_builder.build_validation_error_response(
					serializer.errors, search_id
				)
			
			# Step 3: Check cache (delegated to cache service)
			cache_key = self.cache_service.generate_key(request.data)
			cached_result = self.cache_service.get(cache_key)
			if cached_result:
				# Update cache metadata with current search ID
				cached_result['search_metadata']['performance']['cached'] = True
				cached_result['search_metadata']['performance']['search_id'] = search_id
				cached_result['search_metadata']['cache_key'] = cache_key
				
				self.logger.info(f"[{search_id}] Cache hit", extra={
					'search_id': search_id,
					'cache_key': cache_key
				})
				
				return Response(cached_result, status=status.HTTP_200_OK)
			
			# Step 4: Perform search (delegated to search service)
			search_params = SearchParams(
				locations=serializer.validated_data.get("locations", []),
				radius_miles=serializer.validated_data.get("radius_miles"),
				text=serializer.validated_data.get("text", "")
			)
			search_result = self.search_service.search(search_params)
			
			# Step 5: Build response (delegated to response builder)
			response_data = self.response_builder.build_success_response(
				search_result, search_id
			)
			
			# Step 6: Cache result (delegated to cache service)
			cache_timeout = getattr(settings, 'BUSINESS_SEARCH_CACHE_TIMEOUT', 300)
			self.cache_service.set(cache_key, response_data, cache_timeout)
			
			# Step 7: Log success (delegated to metrics service)
			self.metrics_service.log_success(search_id, search_result)
			
			return Response(response_data, status=status.HTTP_200_OK)
			
		except Exception as e:
			# Error handling (delegated to response builder)
			return self.response_builder.build_server_error_response(e, search_id)

	# Note: All helper methods have been moved to dedicated services
	# following Single Responsibility Principle. The view now only
	# handles HTTP concerns and delegates everything else to services.
	#
	# SOLID Principles Achieved:
	# ✅ S - Single Responsibility: View only handles HTTP
	# ✅ O - Open/Closed: Easy to extend services without changing view
	# ✅ L - Liskov Substitution: Services can be swapped via interfaces
	# ✅ I - Interface Segregation: Focused interfaces for each concern
	# ✅ D - Dependency Inversion: View depends on abstractions, not concretions