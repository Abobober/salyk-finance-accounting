from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView as _TokenObtainPairView,
    TokenRefreshView as _TokenRefreshView,
)


class TokenObtainPairView(_TokenObtainPairView):
    """
    Obtain access and refresh tokens by credentials.

    Expected JSON (POST):
    {
        "email": "user@example.com",
        "password": "your_password"
    }

    Successful response (200):
    {
        "refresh": "<refresh_token>",
        "access": "<access_token>"
    }
    """
    pass


class TokenRefreshView(_TokenRefreshView):
    """
    Refresh an access token using a refresh token.

    Expected JSON (POST):
    {"refresh": "<refresh_token>"}

    Successful response (200):
    {
        "access": "<new_access_token>",
        # when ROTATE_REFRESH_TOKENS=True a new refresh may be returned
        "refresh": "<new_refresh_token>"
    }
    """
    pass


class UserRegistrationView(generics.CreateAPIView):
    """
    Представление для регистрации нового пользователя.
    Доступно без аутентификации.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]  # Разрешаем доступ всем
    
    # Можно переопределить метод, чтобы вернуть кастомный ответ
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Пользователь успешно зарегистрирован. Теперь вы можете войти."},
            status=201,
            headers=headers
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Представление для просмотра и обновления профиля пользователя.
    Доступно только авторизованным пользователям.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Возвращает объект текущего авторизованного пользователя."""
        return self.request.user

class CurrentUserView(APIView):
    """
    Простое представление для получения информации о текущем пользователе.
    Полезно для фронтенда, чтобы проверить, авторизован ли пользователь.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    """
    Blacklist the provided refresh token to log the user out.
    Expected JSON (POST): {"refresh": "<refresh_token>"}
    """
    permission_classes = [IsAuthenticated]

    @parser_classes([JSONParser])
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token_user_id = token.get('user_id')
            if token_user_id is not None and int(token_user_id) != int(request.user.id):
                raise PermissionDenied('Token does not belong to the authenticated user.')
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied:
            raise
        except Exception:
            return Response({'detail': 'Invalid or already blacklisted token.'}, status=status.HTTP_400_BAD_REQUEST)