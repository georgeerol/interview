from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api import BusinessViewSet


def health(request):
	return JsonResponse({"status": "ok"})


router = DefaultRouter()
router.register(r"businesses", BusinessViewSet, basename="business")

urlpatterns = [
	path("health/", health, name="health"),
	path("", include(router.urls)),
]


