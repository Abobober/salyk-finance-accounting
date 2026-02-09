from django.urls import path

from organization.serializers import OrganizationStatusView
from organization.views import OrganizationActivityDetailView, OrganizationActivityListCreateView, OrganizationProfileFinalizeView, OrganizationProfileView
app_name = 'organization'  # Пространство имен для приложения organization
urlpatterns = [
    path('profile/', OrganizationProfileView.as_view(), name='profile'),
    path('finalize/', OrganizationProfileFinalizeView.as_view(), name='finalize_onboarding'),
    path('status/', OrganizationStatusView.as_view(), name='status'),
]