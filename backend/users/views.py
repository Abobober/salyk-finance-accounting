from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserProfileSerializer

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