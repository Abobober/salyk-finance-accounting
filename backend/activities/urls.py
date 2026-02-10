from django.urls import path, include
from rest_framework.routers import DefaultRouter
from activities.views import ActivityCodeViewSet

app_name = 'activities'  # Пространство имен для приложения activities

router = DefaultRouter()
router.register(r"activities", ActivityCodeViewSet, basename="activity")

urlpatterns = [
    path("", include(router.urls)),
]