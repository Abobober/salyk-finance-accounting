from rest_framework import generics, status
from rest_framework.decorators import parser_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import LogoutSerializer, UserProfileSerializer, UserRegistrationSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'User registered successfully. You can now sign in.'},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

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
        except TokenError:
            return Response({'detail': 'Invalid or already blacklisted token.'}, status=status.HTTP_400_BAD_REQUEST)
