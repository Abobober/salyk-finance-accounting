from django.urls import path

from organization.views import (
    OrganizationActivityDetailView,
    OrganizationActivityListCreateView,
    OrganizationProfileFinalizeView,
    OrganizationProfileView,
    OrganizationStatusView,
    TaxPeriodView,
    TaxOfficesListView,
    TaxOfficesUploadView,
)

app_name = 'organization'

urlpatterns = [
    path('profile/', OrganizationProfileView.as_view(), name='profile'),
    path('finalize/', OrganizationProfileFinalizeView.as_view(), name='finalize_onboarding'),
    path('status/', OrganizationStatusView.as_view(), name='status'),
    path('tax-period/', TaxPeriodView.as_view(), name='tax-period'),
    path('tax-offices/', TaxOfficesListView.as_view(), name='tax-offices'),
    path('tax-offices/upload/', TaxOfficesUploadView.as_view(), name='tax-offices-upload'),
    path('activities/', OrganizationActivityListCreateView.as_view(), name='activities'),
    path('activities/<int:pk>/', OrganizationActivityDetailView.as_view(), name='activity_detail'),
]