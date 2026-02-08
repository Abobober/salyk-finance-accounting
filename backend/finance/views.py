from django.db.models import Sum, Q
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .permissions import IsCategoryOwnerOrSystemReadOnly
from .filters import TransactionFilter
from drf_spectacular.utils import extend_schema
from decimal import Decimal


  
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        
        return Category.objects.filter(
            user=self.request.user
        ) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        
        return Transaction.objects.filter(user=self.request.user).select_related('category', 'activity_code')
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    
    @extend_schema(operation_id="finance_transactions_summary")
    
    @action(detail=False, methods=['get'])
    def summary_by_category(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        summary = (
            queryset
            .values('category__name', 'category__category_type')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        return Response(summary)
    
    @extend_schema(operation_id="finance_tax_summary")
    
    @action(detail=False, methods=['get'])
    def tax_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        taxable_queryset = queryset.filter(is_business=True, is_taxable=True)

        summary = taxable_queryset.aggregate(
            taxable_income_cash=Sum('amount', filter=Q(transaction_type='income', payment_method='cash')),
            taxable_income_non_cash=Sum('amount', filter=Q(transaction_type='income', payment_method='non_cash')),
            deductible_expenses=Sum('amount', filter=Q(transaction_type='expense'))
        )
        
        for key, value in summary.items():
            if value is None:
                summary[key] = Decimal(0)

        summary['total_taxable_income'] = summary['taxable_income_cash'] + summary['taxable_income_non_cash']

        return Response(summary)