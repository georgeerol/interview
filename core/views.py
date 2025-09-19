from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Business
from .serializers import BusinessSerializer


class BusinessViewSet(viewsets.ModelViewSet):
	queryset = Business.objects.all().order_by("name")
	serializer_class = BusinessSerializer
	permission_classes = [AllowAny]

	@action(detail=False, methods=["post", "get"], url_path="search")
	def search(self, request):
		# TODO: Implement search based on README spec.

		return Response({"results": []}, status=status.HTTP_200_OK)


