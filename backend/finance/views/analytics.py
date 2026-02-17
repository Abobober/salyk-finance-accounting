"""Analytics views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.constants import DEFAULT_CATEGORY_BREAKDOWN_LIMIT
from finance.permissions import IsOnboardingCompleted
from finance.serializers import (
    CategoryBreakdownResponseSerializer,
    PeriodComparisonResponseSerializer,
    TimeSeriesResponseSerializer,
)
from finance.services.analytics_service import (
    get_category_breakdown,
    get_period_comparison,
    get_time_series_data,
)
from finance.utils import get_preset_dates, parse_date_param


class TimeSeriesAnalyticsView(APIView):
    """Time series data for line/area charts. Supports preset: week, month, year, all_time."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = TimeSeriesResponseSerializer

    def get(self, request):
        period = request.query_params.get('period', 'monthly')
        preset = request.query_params.get('preset')
        transaction_type = request.query_params.get('transaction_type')

        if preset:
            date_from, date_to = get_preset_dates(preset)
            if date_from is None and preset != 'all_time':
                return Response(
                    {'error': f'Invalid preset: {preset}. Use: week, month, year, all_time'},
                    status=400
                )
        else:
            date_from, error = parse_date_param(request.query_params.get('date_from'), 'date_from')
            if error:
                return Response(error, status=400)
            date_to, error = parse_date_param(request.query_params.get('date_to'), 'date_to')
            if error:
                return Response(error, status=400)
            if not date_from and not date_to:
                date_from, date_to = get_preset_dates('month')

        data = get_time_series_data(
            user=request.user,
            period=period,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type
        )

        return Response({
            'period': period,
            'preset': preset,
            'date_from': request.query_params.get('date_from') or (date_from.isoformat() if date_from else None),
            'date_to': request.query_params.get('date_to') or (date_to.isoformat() if date_to else None),
            'data': data,
        })


class CategoryBreakdownAnalyticsView(APIView):
    """Category breakdown for pie/bar charts. Supports preset: week, month, year, all_time."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = CategoryBreakdownResponseSerializer

    def get(self, request):
        preset = request.query_params.get('preset')
        transaction_type = request.query_params.get('transaction_type')

        if preset:
            date_from, date_to = get_preset_dates(preset)
            if date_from is None and preset != 'all_time':
                return Response(
                    {'error': f'Invalid preset: {preset}. Use: week, month, year, all_time'},
                    status=400
                )
        else:
            date_from, error = parse_date_param(request.query_params.get('date_from'), 'date_from')
            if error:
                return Response(error, status=400)
            date_to, error = parse_date_param(request.query_params.get('date_to'), 'date_to')
            if error:
                return Response(error, status=400)
            if not date_from and not date_to:
                date_from, date_to = get_preset_dates('month')

        try:
            limit = int(request.query_params.get('limit', DEFAULT_CATEGORY_BREAKDOWN_LIMIT))
        except ValueError:
            return Response({'error': 'Invalid limit format. Must be an integer.'}, status=400)

        data = get_category_breakdown(
            user=request.user,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type,
            limit=limit
        )

        return Response({
            'preset': preset,
            'date_from': request.query_params.get('date_from') or (date_from.isoformat() if date_from else None),
            'date_to': request.query_params.get('date_to') or (date_to.isoformat() if date_to else None),
            'transaction_type': transaction_type,
            'data': data,
        })


class PeriodComparisonAnalyticsView(APIView):
    """Compare two periods (e.g., this month vs last month)."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = PeriodComparisonResponseSerializer

    def get(self, request):
        p1_from, error = parse_date_param(request.query_params.get('p1_from'), 'p1_from')
        if error:
            return Response(error, status=400)
        p1_to, error = parse_date_param(request.query_params.get('p1_to'), 'p1_to')
        if error:
            return Response(error, status=400)
        p2_from, error = parse_date_param(request.query_params.get('p2_from'), 'p2_from')
        if error:
            return Response(error, status=400)
        p2_to, error = parse_date_param(request.query_params.get('p2_to'), 'p2_to')
        if error:
            return Response(error, status=400)

        if not all([p1_from, p1_to, p2_from, p2_to]):
            return Response({
                'error': 'All parameters required: p1_from, p1_to, p2_from, p2_to (YYYY-MM-DD)'
            }, status=400)

        data = get_period_comparison(
            user=request.user,
            period1_from=p1_from,
            period1_to=p1_to,
            period2_from=p2_from,
            period2_to=p2_to
        )

        return Response(data)
