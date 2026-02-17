from django.urls import path
from .views import GenerateUnifiedTaxReportView

urlpatterns = [
    path("generate-unified-tax/", GenerateUnifiedTaxReportView.as_view()),
]
