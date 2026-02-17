from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .serializers import UnifiedTaxRequestSerializer, UnifiedTaxReportResponseSerializer
from organization.models import OrganizationProfile
from .services.report_data_builder import ReportDataBuilder
from .services.csv_generator import UnifiedTaxCSVGenerator
from .services.ai_validator import AITaxValidator
from django.conf import settings
import os


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

        # Создаём отчёт
        builder = ReportDataBuilder(organization, year, quarter)
        report_data = builder.build_report_data()

        # Генерируем CSV
        file_name = f"unified_tax_{organization.id}_{year}_Q{quarter}.csv"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        csv_generator = UnifiedTaxCSVGenerator(report_data)
        csv_generator.generate(file_path)

        # AI-валидатор
        ai_validator = AITaxValidator()
        ai_comment = ai_validator.validate(report_data)

        # Формируем URL для скачивания CSV
        csv_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, file_name))

        return Response({
            "report_data": report_data,
            "csv_file": csv_url,
            "ai_validation": ai_comment
        })
