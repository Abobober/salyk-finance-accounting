from django.urls import path
from organization.views import OrganizationActivityListCreateView, OrganizationActivityDetailView

app_name = 'activities'  # Пространство имен для приложения activities

urlpatterns = [
    path('', OrganizationActivityListCreateView.as_view(), name='activities'),
    path('<int:pk>/', OrganizationActivityDetailView.as_view(), name='activity_detail'),
]