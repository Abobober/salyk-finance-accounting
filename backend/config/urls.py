"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from users.views import ActivityCodeViewSet, OrganizationProfileView 

router = DefaultRouter()
router.register(r'activity-codes', ActivityCodeViewSet, basename='activity-code')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT эндпоинты для получения и обновления токенов
    # - POST /api/token/        -> obtain access & refresh tokens
    #     Body: {"email": "...", "password": "..."} (or username/password depending on serializer)
    #     Response: {"access": "<jwt>", "refresh": "<jwt>"}
    # - POST /api/token/refresh/-> refresh access token
    #     Body: {"refresh": "<refresh_token>"}
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Путь: /api/users/profile/onboarding/
    path('api/users/', include('users.urls')),

    path('api/users/profile/onboarding/', OrganizationProfileView.as_view(), name='user-onboarding-profile'),

    path('api/finance/', include('finance.urls')),

    path('api/', include(router.urls)),
]
