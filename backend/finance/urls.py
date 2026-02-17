from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    TransactionViewSet,
    DashboardView,
    TimeSeriesAnalyticsView,
    CategoryBreakdownAnalyticsView,
    PeriodComparisonAnalyticsView,
    TaxReportView,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('tax-report/', TaxReportView.as_view(), name='tax-report'),
    path('analytics/time-series/', TimeSeriesAnalyticsView.as_view(), name='analytics-time-series'),
    path('analytics/category-breakdown/', CategoryBreakdownAnalyticsView.as_view(), name='analytics-category-breakdown'),
    path('analytics/period-comparison/', PeriodComparisonAnalyticsView.as_view(), name='analytics-period-comparison'),
] + router.urls
