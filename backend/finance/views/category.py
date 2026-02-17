"""Category views."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from finance.models import Category
from finance.permissions import IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted
from finance.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD operations."""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
