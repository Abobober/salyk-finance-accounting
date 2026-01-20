from django.urls import path
from . import views

app_name = 'users'  # Пространство имен для приложения users
urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
]