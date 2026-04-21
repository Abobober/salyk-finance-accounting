from django.urls import path

from .views import GenerateUnifiedTaxReportView

urlpatterns = [
    path('generate-unified-tax/', GenerateUnifiedTaxReportView.as_view(), name='generate-unified-tax'),
    path('generate-sti-091/', GenerateUnifiedTaxReportView.as_view(), name='generate-sti-091'),
]
