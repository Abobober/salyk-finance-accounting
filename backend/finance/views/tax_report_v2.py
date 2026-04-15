"""Canonical tax report v2 view."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.permissions import IsOnboardingCompleted
from finance.serializers import TaxReportV2ResponseSerializer
from finance.services.tax_report_v2_service import (
    TaxReportV2ValidationError,
    build_tax_report_v2,
)


class TaxReportV2View(APIView):
    """Canonical tax report endpoint for downstream consumers."""

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = TaxReportV2ResponseSerializer

    def get(self, request):
        try:
            data = build_tax_report_v2(request.user, request.query_params)
        except TaxReportV2ValidationError as exc:
            return Response(exc.detail, status=400)
        return Response(data)
