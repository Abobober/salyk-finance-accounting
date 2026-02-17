import os
from urllib.parse import urljoin

from django.conf import settings
from drf_spectacular.utils import extend_schema
from organization.models import OrganizationProfile
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UnifiedTaxRequestSerializer, UnifiedTaxReportResponseSerializer
from .services.ai_validator import AITaxValidator
from .services.pdf_generator import UnifiedTaxPDFGenerator
from .services.report_data_builder import ReportDataBuilder


class GenerateUnifiedTaxReportView(APIView):
    serializer_class = UnifiedTaxRequestSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UnifiedTaxRequestSerializer,
        responses={200: UnifiedTaxReportResponseSerializer},
    )
    def post(self, request):
        serializer = UnifiedTaxRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        year = serializer.validated_data["year"]
        quarter = serializer.validated_data["quarter"]

        try:
            organization = OrganizationProfile.objects.get(user=request.user)
        except OrganizationProfile.DoesNotExist:
            return Response({"error": "Organization profile not found"}, status=404)

        builder = ReportDataBuilder(organization, year, quarter)
        report_data = builder.build_report_data()

        file_name = f"unified_tax_{organization.id}_{year}_Q{quarter}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        template_path = os.path.join(
            settings.BASE_DIR, "tax_reports", "templates", "unified_tax_blank.pdf"
        )

        try:
            pdf_generator = UnifiedTaxPDFGenerator(report_data, template_path=template_path)
            pdf_generator.generate(file_path)
        except Exception as exc:
            return Response(
                {"error": f"Failed to generate PDF report: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ai_validator = AITaxValidator()
        ai_comment = ai_validator.validate(report_data)

        pdf_url = request.build_absolute_uri(urljoin(settings.MEDIA_URL, file_name))
        return Response(
            {
                "report_data": report_data,
                "pdf_file": pdf_url,
                "ai_validation": ai_comment,
            }
        )
