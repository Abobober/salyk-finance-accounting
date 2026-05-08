"""Transaction views."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from finance.filters import TransactionFilter
from finance.models import Transaction
from finance.permissions import IsOnboardingCompleted
from finance.serializers import TransactionSerializer
from finance.services.transaction_service import TransactionService


class TransactionViewSet(viewsets.ModelViewSet):
    """Transaction CRUD operations."""

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    filterset_class = TransactionFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['transaction_date', 'amount', 'created_at', 'activity_code', 'activity_code__name']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        return (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related('category', 'activity_code', 'user')
            .order_by('-transaction_date', '-created_at')
        )

    def perform_create(self, serializer):
        instance = TransactionService.create_transaction(
            user=self.request.user,
            validated_data=serializer.validated_data
        )
        serializer.instance = instance

    def perform_update(self, serializer):
        instance = TransactionService.update_transaction(
            instance=serializer.instance,
            validated_data=serializer.validated_data
        )
        serializer.instance = instance
