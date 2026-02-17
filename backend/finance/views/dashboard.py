"""Dashboard views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.permissions import IsOnboardingCompleted
from finance.serializers import DashboardResponseSerializer
from finance.services.dashboard_service import get_dashboard_data


class DashboardView(APIView):
    """Single endpoint for dashboard data."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = DashboardResponseSerializer

    def get(self, request):
        data = get_dashboard_data(request.user)
        return Response(data)
