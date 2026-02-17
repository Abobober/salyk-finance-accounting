from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.models import OrganizationActivity, OrganizationProfile
from organization.serializers import (
    OrganizationProfileSerializer,
    OrganizationActivitySerializer,
    OnboardingFinalizeSerializer,
    OrganizationStatusSerializer,
    TaxPeriodResponseSerializer,
)

class OrganizationProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint для получения/обновления налогового профиля текущего пользователя.
    Используется для прохождения онбординга.
    """
    serializer_class = OrganizationProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        
        """Возвращает или создает профиль для текущего пользователя."""
        # Используем get_or_create, чтобы гарантировать наличие профиля при первом обращении
        profile, _ = OrganizationProfile.objects.get_or_create(user=self.request.user)
        return profile

    # используем RetrieveUpdateAPIView, POST запросы здесь не нужны, 
    # онбординг завершается через PUT/PATCH, который вызывает метод update() сериализатора.

class OrganizationActivityListCreateView(generics.ListCreateAPIView):
    """API endpoint для добавления видов деятельности в профиль пользователя."""
    serializer_class = OrganizationActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrganizationActivity.objects.none()
        return OrganizationActivity.objects.filter(profile=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.organization)


class OrganizationActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint для получения/обновления/удаления конкретного вида деятельности в профиле пользователя."""
    serializer_class = OrganizationActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrganizationActivity.objects.none()
        return OrganizationActivity.objects.filter(profile=self.request.user.organization)
    

class OrganizationProfileFinalizeView(generics.UpdateAPIView):
    """API endpoint для финализации онбординга - проверяет, что все данные заполнены и ставит флаг is_onboarded."""
    serializer_class = OnboardingFinalizeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.organization

class OrganizationStatusView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationStatusSerializer

    def get(self, request):
        profile, _ = OrganizationProfile.objects.get_or_create(user=request.user)
        data = {
            "onboarding_status": profile.onboarding_status,
            "is_completed": profile.onboarding_status == OrganizationProfile.OnboardingStatus.COMPLETED
        }
        return Response(data)


class TaxPeriodView(APIView):
    """Get current tax period dates based on organization's tax period settings."""

    permission_classes = [IsAuthenticated]
    serializer_class = TaxPeriodResponseSerializer

    def get(self, request):
        profile = request.user.organization
        
        if not profile.tax_period_type:
            return Response({
                'error': 'Tax period is not configured for this organization.'
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
        except ValueError as e:
            return Response({'error': str(e)}, status=400)