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
from drf_spectacular.utils import extend_schema


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint

    Path: POST /api/users/register/
    - Auth: not required
    - Body (JSON): {"email": "user@example.com", "password": "string", "first_name": "opt", "last_name": "opt"}
    - Response: 201 Created with message: {"message": "Пользователь успешно зарегистрирован. Теперь вы можете войти."}
    - Frontend should redirect to login on success.
    """
    @extend_schema(responses={201: UserProfileSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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
    User profile endpoint

    Path: /api/users/profile/
    - Methods: GET, PUT, PATCH
    - Auth: required
    - GET response: current user profile object (fields depend on serializer)
    - PUT/PATCH body: partial or full user object to update (e.g. first_name, last_name, email)
    - Response: 200 OK with updated profile
    - Frontend: use this for profile page and profile edits.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Возвращает объект текущего авторизованного пользователя."""
        return self.request.user

class CurrentUserView(APIView):
    """
    Current user check endpoint

    Path: GET /api/users/me/
    - Auth: required
    - Returns: current authenticated user serialized (use to confirm login and load quick profile info)
    - Response: 200 OK with user object
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    @extend_schema(
        summary="Данные текущего юзера",
        responses={200: UserProfileSerializer}
    )
    
    def get(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    """
    Logout endpoint

    Path: POST /api/users/logout/
    - Auth: required
    - Body (JSON): {"refresh": "<refresh_token>"}
    - Response: 204 No Content on success
    - Errors: 400 if token is missing/invalid; 403 if token belongs to another user
    - Frontend flow: when logging out, discard local tokens and call this endpoint with the refresh token to blacklist it server-side.
    """
    permission_classes = [IsAuthenticated]
    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"refresh": {"type": "string"}},
                "required": ["refresh"]
            }
        },
        responses={204: None}
    )

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