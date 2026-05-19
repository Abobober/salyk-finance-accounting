from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
import os
import json
import pandas as pd

from organization.models import OrganizationActivity, OrganizationProfile
from organization.serializers import (
    OnboardingFinalizeSerializer,
    OrganizationActivitySerializer,
    OrganizationProfileSerializer,
    OrganizationStatusSerializer,
    TaxPeriodResponseSerializer,
)
from organization.services import get_or_create_organization_profile


class OrganizationProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_or_create_organization_profile(self.request.user)


class OrganizationActivityListCreateView(generics.ListCreateAPIView):
    serializer_class = OrganizationActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrganizationActivity.objects.none()
        profile = get_or_create_organization_profile(self.request.user)
        return OrganizationActivity.objects.filter(profile=profile)

    def perform_create(self, serializer):
        serializer.save(profile=get_or_create_organization_profile(self.request.user))


class OrganizationActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrganizationActivity.objects.none()
        profile = get_or_create_organization_profile(self.request.user)
        return OrganizationActivity.objects.filter(profile=profile)


class OrganizationProfileFinalizeView(generics.UpdateAPIView):
    serializer_class = OnboardingFinalizeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_or_create_organization_profile(self.request.user)


class OrganizationStatusView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationStatusSerializer

    def get(self, request):
        profile = get_or_create_organization_profile(request.user)
        data = {
            "onboarding_status": profile.onboarding_status,
            "is_completed": profile.onboarding_status == OrganizationProfile.OnboardingStatus.COMPLETED,
        }
        return Response(data)


class TaxPeriodView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxPeriodResponseSerializer

    def get(self, request):
        profile = get_or_create_organization_profile(request.user)

        if not profile.tax_period_type:
            return Response({
                'error': 'Tax period is not configured for this organization.',
            }, status=400)

        try:
            from organization.tax_period_utils import get_current_tax_period_start_end, get_next_tax_period_start

            period_start, period_end = get_current_tax_period_start_end(profile)
            next_period_start = get_next_tax_period_start(profile)

            return Response({
                'tax_period_type': profile.tax_period_type,
                'tax_period_preset': profile.tax_period_preset,
                'tax_period_custom_day': profile.tax_period_custom_day,
                'current_period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat(),
                },
                'next_period_start': next_period_start.isoformat(),
            })
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)


class TaxOfficesListView(APIView):
    """Возвращает список налоговых органов из статического JSON-файла.

    Ожидается файл `data/tax_offices.json` рядом с приложением `organization`.
    Поддерживается параметр `q` для поиска по коду или наименованию.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.GET.get('q') or '').strip().lower()
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        data_path = os.path.join(data_dir, 'tax_offices.json')

        if not os.path.exists(data_path):
            return Response([], status=200)

        try:
            with open(data_path, 'r', encoding='utf-8') as fh:
                offices = json.load(fh)
        except Exception:
            return Response([], status=200)

        if q:
            offices = [o for o in offices if q in (o.get('code') or '').lower() or q in (o.get('name') or '').lower()]

        return Response(offices)


class TaxOfficesUploadView(APIView):
    """Upload an Excel file with tax offices and replace the JSON data.

    Only admin users are allowed to call this endpoint.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'Missing file'}, status=400)

        if not uploaded.name.lower().endswith(('.xlsx', '.xls')):
            return Response({'error': 'Unsupported file type'}, status=400)

        try:
            df = pd.read_excel(uploaded, header=None, engine='openpyxl', dtype=str)
        except Exception as exc:
            return Response({'error': f'Failed to read Excel: {exc}'}, status=400)

        try:
            from . import autoload_tax_offices

            deduped = autoload_tax_offices._parse_dataframe(df)

            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            os.makedirs(data_dir, exist_ok=True)
            data_path = os.path.join(data_dir, 'tax_offices.json')
            with open(data_path, 'w', encoding='utf-8') as fh:
                json.dump(deduped, fh, ensure_ascii=False, indent=2)

            return Response(deduped)
        except Exception as exc:
            return Response({'error': f'Failed to process file: {exc}'}, status=500)
