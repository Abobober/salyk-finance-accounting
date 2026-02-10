from django.urls import path
from organization.views import OrganizationActivityDetailView, OrganizationActivityListCreateView, OrganizationProfileFinalizeView, OrganizationProfileView, OrganizationStatusView

app_name = 'organization'  # Пространство имен для приложения organization
urlpatterns = [
    path('profile/', OrganizationProfileView.as_view(), name='profile'),
    path('finalize/', OrganizationProfileFinalizeView.as_view(), name='finalize_onboarding'),
    path('status/', OrganizationStatusView.as_view(), name='status'),
    path('activities/', OrganizationActivityListCreateView.as_view(), name='activities'),
    path('activities/<int:pk>/', OrganizationActivityDetailView.as_view(), name='activity_detail'),
]