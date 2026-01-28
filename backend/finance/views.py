from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db import models

from .models import Transaction, Category
from .serializers import (
    TransactionSerializer, 
    CategorySerializer,
    TransactionSummarySerializer
)



class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления категориями.
    Позволяет создавать, просматривать, обновлять и удалять категории.
    """
    
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Возвращает только категории текущего пользователя + системные категории.
        """
        user = self.request.user
        
        # Берем категории пользователя и системные категории
        return Category.objects.filter(
            models.Q(user=user) | models.Q(is_system=True)
        ).distinct()
    
    def perform_create(self, serializer):
        """
        При создании категории автоматически привязываем ее к текущему пользователю.
        """
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления финансовыми операциями (доходами/расходами).
    Реализует полный CRUD.
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Возвращает только транзакции текущего пользователя.
        Можно фильтровать по типу, дате, категории.
        """
        queryset = Transaction.objects.filter(user=self.request.user)
        
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
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Возвращает сводку по транзакциям за период.
        
        Параметры:
        - period: 'day', 'week', 'month', 'year' (по умолчанию 'month')
        - date_from, date_to: конкретные даты
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
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Возвращает транзакции сгруппированные по категориям.
        Полезно для построения графиков.
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