"""Dashboard views."""

from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.permissions import IsOnboardingCompleted
from finance.serializers import DashboardResponseSerializer
from finance.services.dashboard_service import dashboard_cache_key, get_dashboard_data


class DashboardView(APIView):
    """Single endpoint for dashboard data; cached and invalidated on transaction changes."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = DashboardResponseSerializer

    def get(self, request):
        key = dashboard_cache_key(request.user.id)
        data = cache.get(key)
        if data is None:
            data = get_dashboard_data(request.user)
            ttl = getattr(settings, 'DASHBOARD_CACHE_TTL', 45)
            cache.set(key, data, ttl)
        return Response(data)
