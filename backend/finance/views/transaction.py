"""Transaction views."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    def perform_destroy(self, instance):
        TransactionService.soft_delete(instance, self.request.user)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """Восстановить транзакцию после мягкого удаления (только владелец)."""
        instance = (
            Transaction.all_objects
            .filter(pk=pk, user=request.user)
            .exclude(deleted_at__isnull=True)
            .first()
        )
        if instance is None:
            return Response({'detail': 'Транзакция не найдена или уже активна.'}, status=status.HTTP_404_NOT_FOUND)
        TransactionService.restore_transaction(instance, request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
