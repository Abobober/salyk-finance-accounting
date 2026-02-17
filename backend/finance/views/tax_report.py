"""Tax report view: generate report for any chosen period or org's current tax period."""

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.permissions import IsOnboardingCompleted
from finance.serializers import TaxReportResponseSerializer
from finance.services.tax_report_service import build_tax_report
from finance.utils import get_preset_dates, parse_date_param


class TaxReportView(APIView):
    """
    Tax report for a chosen period.
    
    Query params:
    - date_from, date_to: explicit period (YYYY-MM-DD)
    - preset: week, month, year, all_time (same as analytics)
    - use_org_tax_period: if true, use organization's current tax period (ignores dates/preset)
    """

    permission_classes = [IsAuthenticated, IsOnboardingCompleted]
    serializer_class = TaxReportResponseSerializer

    def get(self, request):
        use_org = request.query_params.get('use_org_tax_period', '').lower() in ('true', '1', 'yes')

        if use_org:
            profile = request.user.organization
            if not profile.tax_period_type:
                return Response(
                    {'error': 'Tax period is not configured. Set it in organization profile or use date_from/date_to.'},
                    status=400
                )
            try:
                from organization.tax_period_utils import get_current_tax_period_start_end
                date_from, date_to = get_current_tax_period_start_end(profile)
            except ValueError as e:
                return Response({'error': str(e)}, status=400)
        else:
            preset = request.query_params.get('preset')
            if preset == 'all_time':
                date_to = timezone.now().date()
                date_from = date_to.replace(year=date_to.year - 50, month=1, day=1)
            elif preset:
                date_from, date_to = get_preset_dates(preset)
                if date_from is None:
                    return Response(
                        {'error': f'Invalid preset: {preset}. Use: week, month, year, all_time'},
                        status=400
                    )
            else:
                date_from, err = parse_date_param(request.query_params.get('date_from'), 'date_from')
                if err:
                    return Response(err, status=400)
                date_to, err = parse_date_param(request.query_params.get('date_to'), 'date_to')
                if err:
                    return Response(err, status=400)
                if (date_from or date_to) and not (date_from and date_to):
                    return Response(
                        {'error': 'Provide both date_from and date_to, or use preset, or use_org_tax_period=true'},
                        status=400
                    )
                if not date_from and not date_to:
                    date_from, date_to = get_preset_dates('month')

        data = build_tax_report(request.user, date_from, date_to)
        return Response(data)
