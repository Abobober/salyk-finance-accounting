from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.models import OrganizationActivity, OrganizationProfile
from organization.serializers import OrganizationProfileSerializer, OrganizationActivitySerializer, OnboardingFinalizeSerializer

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
        return OrganizationActivity.objects.filter(profile=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.organization)


class OrganizationActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint для получения/обновления/удаления конкретного вида деятельности в профиле пользователя."""
    serializer_class = OrganizationActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrganizationActivity.objects.filter(profile=self.request.user.organization)
    

class OrganizationProfileFinalizeView(generics.UpdateAPIView):
    """API endpoint для финализации онбординга - проверяет, что все данные заполнены и ставит флаг is_onboarded."""
    serializer_class = OnboardingFinalizeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.organization

class OrganizationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = OrganizationProfile.objects.get_or_create(user=request.user)
        return Response({
            "onboarding_status": profile.onboarding_status,
            "is_completed": profile.onboarding_status == OrganizationProfile.OnboardingStatus.COMPLETED
        })