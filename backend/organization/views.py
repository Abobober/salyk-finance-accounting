from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
