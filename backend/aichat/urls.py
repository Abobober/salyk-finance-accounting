# aichat/urls.py
from django.urls import path
from .views import OpenRouterView

urlpatterns = [
    path("consult/", OpenRouterView.as_view(), name="ai-consulting"),
]
