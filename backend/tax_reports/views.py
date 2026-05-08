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
from .services.report_data_builder import STI091ReportDataBuilder
from .template_config import TemplateNotFoundError, get_template_path


class GenerateUnifiedTaxReportView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UnifiedTaxRequestSerializer

    @extend_schema(
        request=UnifiedTaxRequestSerializer,
        responses={200: UnifiedTaxReportResponseSerializer},
    )
    def post(self, request):
        serializer = UnifiedTaxRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        year = serializer.validated_data['year']
        quarter = serializer.validated_data['quarter']

        try:
            organization = OrganizationProfile.objects.get(user=request.user)
        except OrganizationProfile.DoesNotExist:
            return Response({'error': 'Organization profile not found'}, status=404)

        builder = STI091ReportDataBuilder(
            organization,
            year,
            quarter,
            report_kind=serializer.validated_data['report_kind'],
            tin=serializer.validated_data.get('tin', ''),
            taxpayer_name=serializer.validated_data.get('taxpayer_name', ''),
            tax_office=serializer.validated_data.get('tax_office', ''),
            contact_phone=serializer.validated_data.get('contact_phone', ''),
            activity_line_map=serializer.validated_data.get('activity_line_map', {}),
            current_period_advance_payments=serializer.validated_data.get('current_period_advance_payments', []),
            previous_period_advance_offsets=serializer.validated_data.get('previous_period_advance_offsets', []),
        )
        report_data = builder.build_report_data()
        verbal_report = self._build_verbal_report(report_data)

        issue_count = len(report_data['issues'])
        error_count = sum(1 for issue in report_data['issues'] if issue['severity'] == 'error')
        if error_count:
            validation_summary = f'Обнаружено ошибок: {error_count}, предупреждений: {issue_count - error_count}.'
        elif issue_count:
            validation_summary = f'Отчет сформирован с предупреждениями: {issue_count}.'
        else:
            validation_summary = 'Отчет сформирован и готов к подаче.'

        pdf_url = None
        if serializer.validated_data.get('generate_pdf', True):
            file_name = f"sti_091_{organization.id}_{year}_Q{quarter}.pdf"
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            try:
                template_path = get_template_path(
                    report_type='unified_tax',
                    tax_regime=organization.tax_regime,
                    period_key='quarterly',
                )
            except TemplateNotFoundError as exc:
                report_data['issues'].append({
                    'code': 'template_not_found',
                    'severity': 'warning',
                    'message': 'Не найден PDF-шаблон формы STI-091.',
                    'details': {'error': str(exc)},
                })
                validation_summary = validation_summary + ' PDF не сгенерирован: отсутствует шаблон.'
            else:
                try:
                    pdf_generator = UnifiedTaxPDFGenerator(report_data, template_path=template_path)
                    pdf_generator.generate(file_path)
                    pdf_url = request.build_absolute_uri(urljoin(settings.MEDIA_URL, file_name))
                except Exception as exc:
                    report_data['issues'].append({
                        'code': 'pdf_generation_failed',
                        'severity': 'warning',
                        'message': 'Не удалось сформировать PDF-версию отчета.',
                        'details': {'error': str(exc)},
                    })
                    validation_summary = validation_summary + ' PDF не сгенерирован из-за технической ошибки.'

        ai_text = AITaxValidator().validate(report_data)
        ai_status = 'unavailable' if ai_text.lower().startswith('ai-проверка недоступна') else 'ok'

        return Response(
            {
                'pdf_file': pdf_url,
                'verbal_report': verbal_report,
                'ai_validation': ai_text,
                'ai_validation_status': ai_status,
                'validation_summary': validation_summary,
            },
            status=status.HTTP_200_OK,
        )

    def _build_verbal_report(self, report_data):
        cells = report_data.get('cells', {})
        header = report_data.get('header', {})
        period = report_data.get('period', {})
        issues = report_data.get('issues', [])
        errors = [item for item in issues if item.get('severity') == 'error']
        warnings = [item for item in issues if item.get('severity') == 'warning']

        lines = [
            f"Форма {report_data.get('form_code')}-{report_data.get('form_version')} за {report_data.get('year')} Q{report_data.get('quarter')} ({report_data.get('report_kind')}).",
            f"Налогоплательщик: {header.get('103') or '-'} (ИНН: {header.get('102') or '-'}).",
            f"Период: {period.get('start')} - {period.get('end')}.",
            f"Итоговая налоговая база (ячейка 186): {cells.get('186', '0.00')}.",
            f"Итоговая сумма налога (ячейка 187): {cells.get('187', '0.00')}.",
            f"Ошибок: {len(errors)}, предупреждений: {len(warnings)}.",
        ]

        if issues:
            lines.append('Замечания: ' + '; '.join(item.get('message', '') for item in issues[:5]))
        else:
            lines.append('Замечаний не выявлено, отчет готов к подаче.')

        return ' '.join(lines)
