from typing import Any
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter



from .models import Transaction, Category
from .serializers import (
    TransactionSerializer, 
    CategorySerializer,
    TransactionSummarySerializer
)
from .swagger_schemas import (
    BY_CATEGORY_RESP,
    CATEGORY_LIST_RESP,
    CATEGORY_DETAIL_RESP,
    CATEGORY_CREATE_REQ,
    CATEGORY_CREATE_RESP,
    CATEGORY_UPDATE_RESP,
    CATEGORY_DELETE_RESP,
    TRANSACTION_LIST_PARAMS,
    TRANSACTION_LIST_RESP,
    TRANSACTION_DETAIL_RESP,
    TRANSACTION_CREATE_REQ,
    TRANSACTION_CREATE_RESP,
    TRANSACTION_UPDATE_RESP,
    TRANSACTION_DELETE_RESP,
    SUMMARY_PARAMS,
    SUMMARY_RESP,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for categories CRUD.
    """
    
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Category.objects.none()
        user = self.request.user
        return Category.objects.filter(Q(user=user) | Q(is_system=True)).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        # Не позволяем менять системные категории
        if obj.is_system and obj.user is None:
            raise PermissionDenied("Системные категории менять нельзя.")
        # Также не позволяем менять чужую категорию
        if obj.user and obj.user != self.request.user:
            raise PermissionDenied("Нельзя менять чужую категорию.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_system and instance.user is None:
            raise PermissionDenied("Системные категории удалять нельзя.")
        if instance.user and instance.user != self.request.user:
            raise PermissionDenied("Нельзя удалять чужую категорию.")
        instance.delete()

    @swagger_auto_schema(operation_description="List categories", responses=CATEGORY_LIST_RESP)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a category", responses=CATEGORY_DETAIL_RESP)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a category", request_body=CATEGORY_CREATE_REQ, responses=CATEGORY_CREATE_RESP)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a category", request_body=CATEGORY_CREATE_REQ, responses=CATEGORY_UPDATE_RESP)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a category", request_body=CATEGORY_CREATE_REQ, responses=CATEGORY_UPDATE_RESP)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a category", responses=CATEGORY_DELETE_RESP)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления финансовыми операциями (доходами/расходами).
    
    Permissions: IsAuthenticated
    

    Features:
    - CRUD операций (доход/расход)
    - Фильтрация по типу, категории и дате
    - Получение сводки и группировка по категориям
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]

    ordering_fields = [
        'transaction_date',
        'amount',
        'created_at'
    ]

    ordering = ['-transaction_date']
    
    def get_queryset(self):
        """
        Возвращает только транзакции текущего пользователя.
        
        Query parameters:
        - type: 'income' или 'expense' (необязательно)
        - category_id: ID категории (необязательно)
        - date_from: начало периода YYYY-MM-DD (необязательно)
        - date_to: конец периода YYYY-MM-DD (необязательно)
        """

        # Short-circuit for drf_yasg schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            # Safety check, although permission_classes=IsAuthenticated should prevent this
            return Transaction.objects.none()

        queryset = Transaction.objects.filter(user=user)
        
        # Фильтрация по типу операции (income/expense)
        transaction_type = self.request.query_params.get('type')
        if transaction_type in ['income', 'expense']:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Фильтрация по категории
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Фильтрация по дате (с)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        
        # Фильтрация по дате (по)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        # Сортировка по дате операции (сначала новые)
        return queryset.order_by('-transaction_date', '-created_at')
    
    def perform_create(self, serializer):
        """
        При создании транзакции автоматически привязываем ее к текущему пользователю.
        """
        serializer.save(user=self.request.user)

    @swagger_auto_schema(operation_description="List transactions", manual_parameters=TRANSACTION_LIST_PARAMS, responses=TRANSACTION_LIST_RESP)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a transaction", responses=TRANSACTION_DETAIL_RESP)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a transaction", request_body=TRANSACTION_CREATE_REQ, responses=TRANSACTION_CREATE_RESP)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a transaction", request_body=TRANSACTION_CREATE_REQ, responses=TRANSACTION_UPDATE_RESP)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a transaction", request_body=TRANSACTION_CREATE_REQ, responses=TRANSACTION_UPDATE_RESP)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a transaction", responses=TRANSACTION_DELETE_RESP)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(method='get', manual_parameters=SUMMARY_PARAMS, responses=SUMMARY_RESP)
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Возвращает сводку по транзакциям за период.
        
        Query parameters:
        - period: 'day', 'week', 'month', 'year' (default='month')
        - date_from: YYYY-MM-DD (overrides period if provided)
        - date_to: YYYY-MM-DD (overrides period if provided)

        Примеры использования:
        - /api/finance/transactions/summary/?period=month
        - /api/finance/transactions/summary/?date_from=2024-01-01&date_to=2024-01-31
        
        Возвращает:
        - total_income: общая сумма доходов
        - total_expense: общая сумма расходов
        - net_profit: чистая прибыль (доходы - расходы)
        - transaction_count: количество операций
        - period {date_from, date_to}
        """
        queryset = self.get_queryset()
        
        # Определяем период
        period = request.query_params.get('period', 'month')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            # Если даты не указаны, используем период
            today = timezone.now().date()
            
            if period == 'day':
                date_from = today
                date_to = today
            elif period == 'week':
                date_from = today - timedelta(days=7)
                date_to = today
            elif period == 'month':
                date_from = today.replace(day=1)
                date_to = today
            elif period == 'year':
                date_from = today.replace(month=1, day=1)
                date_to = today
            else:
                # По умолчанию - текущий месяц
                date_from = today.replace(day=1)
                date_to = today
        
        # Фильтруем по дате
        queryset = queryset.filter(
            transaction_date__gte=date_from,
            transaction_date__lte=date_to
        )
        
        # Рассчитываем итоги
        income_data = queryset.filter(transaction_type='income').aggregate(
            total=Sum('amount')
        )
        expense_data = queryset.filter(transaction_type='expense').aggregate(
            total=Sum('amount')
        )
        
        total_income = income_data['total'] or 0
        total_expense = expense_data['total'] or 0
        net_profit = total_income - total_expense
        
        # Создаем сводку
        summary = {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'transaction_count': queryset.count(),
            'period': {
                'date_from': date_from,
                'date_to': date_to
            }
        }
        
        serializer = TransactionSummarySerializer(summary)
        return Response(serializer.data)
    
    @swagger_auto_schema(responses=BY_CATEGORY_RESP)
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Возвращает транзакции сгруппированные по категориям.

        Query parameters:
        - type: 'income'|'expense' (optional)
        - date_from: YYYY-MM-DD (optional)
        - date_to: YYYY-MM-DD (optional)

        Request example:
        - GET /api/finance/transactions/by_category/?date_from=2026-01-01&date_to=2026-01-31&type=expense

        Response example:
        [
            {"category__id": 5, "category__name": "Food", "transaction_type": "expense", "total_amount": "250.00", "transaction_count": 10},
            {"category__id": null, "category__name": null, "transaction_type": "income", "total_amount": "100.00", "transaction_count": 1}
        ]
        """
        
        queryset = self.get_queryset()
        
        # Группируем по категориям
        category_data = queryset.values(
            'category__id', 
            'category__name',
            'transaction_type'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')
    
        return Response(category_data)
