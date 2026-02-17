from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .permissions import IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted
from .filters import TransactionFilter
from .services.transaction_service import TransactionService
from .services.category_service import CategoryService
from .services.dashboard_service import (
    dashboard_cache_key,
    get_dashboard_data,
)
from .services.analytics_service import (
    get_time_series_data,
    get_category_breakdown,
    get_period_comparison,
)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsCategoryOwnerOrSystemReadOnly, IsOnboardingCompleted]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        return Category.objects.filter(user=self.request.user) | Category.objects.filter(is_system=True)

    def perform_create(self, serializer):
        instance = CategoryService.create_category(
            user=self.request.user,
            validated_data=serializer.validated_data
        )
        serializer.instance = instance

    def perform_update(self, serializer):
        instance = CategoryService.update_category(
            instance=serializer.instance,
            validated_data=serializer.validated_data
        )
        serializer.instance = instance


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    filterset_class = TransactionFilter
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        return (Transaction.objects
                .filter(user=self.request.user)
                .select_related('category', 'activity_code', 'user')
                .order_by('-transaction_date', '-created_at'))

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

    def summary_by_category(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        summary = (
            queryset
            .values('category__name', 'category__category_type')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return Response(summary)


class DashboardView(APIView):
    """Stage 4: single endpoint for all dashboard data; cached 30–60s; invalidated on transaction create/update."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]

    def get(self, request):
        key = dashboard_cache_key(request.user.id)
        data = cache.get(key)
        if data is None:
            data = get_dashboard_data(request.user)
            ttl = getattr(settings, 'DASHBOARD_CACHE_TTL', 45)
            cache.set(key, data, ttl)
        return Response(data)


class TimeSeriesAnalyticsView(APIView):
    """
    Time series data for line/area charts.
    GET /api/finance/analytics/time-series/?period=monthly&date_from=2024-01-01&date_to=2024-12-31&transaction_type=income
    """
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]

    def get(self, request):
        period = request.query_params.get('period', 'monthly')  # daily, monthly, yearly
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        transaction_type = request.query_params.get('transaction_type')  # income, expense, or None
        
        date_from = None
        date_to = None
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date_from format. Use YYYY-MM-DD'}, status=400)
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date_to format. Use YYYY-MM-DD'}, status=400)
        
        data = get_time_series_data(
            user=request.user,
            period=period,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type
        )
        
        return Response({
            'period': period,
            'date_from': date_from_str,
            'date_to': date_to_str,
            'data': data,
        })


class CategoryBreakdownAnalyticsView(APIView):
    """
    Category breakdown for pie/bar charts.
    GET /api/finance/analytics/category-breakdown/?date_from=2024-01-01&date_to=2024-12-31&transaction_type=expense&limit=10
    """
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]

    def get(self, request):
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        transaction_type = request.query_params.get('transaction_type')
        limit = int(request.query_params.get('limit', 10))
        
        date_from = None
        date_to = None
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date_from format. Use YYYY-MM-DD'}, status=400)
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date_to format. Use YYYY-MM-DD'}, status=400)
        
        data = get_category_breakdown(
            user=request.user,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type,
            limit=limit
        )
        
        return Response({
            'date_from': date_from_str,
            'date_to': date_to_str,
            'transaction_type': transaction_type,
            'data': data,
        })


class PeriodComparisonAnalyticsView(APIView):
    """
    Compare two periods (e.g., this month vs last month).
    GET /api/finance/analytics/period-comparison/?p1_from=2024-01-01&p1_to=2024-01-31&p2_from=2024-02-01&p2_to=2024-02-29
    """
    permission_classes = [IsAuthenticated, IsOnboardingCompleted]

    def get(self, request):
        p1_from_str = request.query_params.get('p1_from')
        p1_to_str = request.query_params.get('p1_to')
        p2_from_str = request.query_params.get('p2_from')
        p2_to_str = request.query_params.get('p2_to')
        
        if not all([p1_from_str, p1_to_str, p2_from_str, p2_to_str]):
            return Response({
                'error': 'All parameters required: p1_from, p1_to, p2_from, p2_to (YYYY-MM-DD)'
            }, status=400)
        
        try:
            p1_from = datetime.strptime(p1_from_str, '%Y-%m-%d').date()
            p1_to = datetime.strptime(p1_to_str, '%Y-%m-%d').date()
            p2_from = datetime.strptime(p2_from_str, '%Y-%m-%d').date()
            p2_to = datetime.strptime(p2_to_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        data = get_period_comparison(
            user=request.user,
            period1_from=p1_from,
            period1_to=p1_to,
            period2_from=p2_from,
            period2_to=p2_to
        )
        
        return Response(data)
