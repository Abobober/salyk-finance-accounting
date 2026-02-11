# aichat/urls.py
from django.urls import path
from .views import OpenRouterView

urlpatterns = [
    path("chat/", OpenRouterView.as_view(), name="ai-chat"),
]
