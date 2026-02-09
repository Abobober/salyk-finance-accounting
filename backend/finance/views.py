from django.db.models import Sum, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .permissions import IsCategoryOwnerOrSystemReadOnly
from .filters import TransactionFilter


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category', 'activity_code')

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
