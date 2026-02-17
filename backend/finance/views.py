from django.db.models import Sum, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .permissions import IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted
from .filters import TransactionFilter
from finance.services.transaction_service import TransactionService


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        TransactionService.create_transaction(
            user=self.request.user,
            validated_data=serializer.validated_data
    )

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    filterset_class = TransactionFilter
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        return (Transaction.objects
                .filter(user=self.request.user).
                select_related('category', 'activity_code', 'user')
                .order_by('-transaction_date', '-created_at'))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def summary_by_category(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        summary = (
            queryset
            .values('category__name', 'category__category_type')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return Response(summary)
