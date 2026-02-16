from datetime import timezone
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import TelegramBindingToken
from .permissions import IsTelegramBot

User = get_user_model()

class GetTelegramLinkView(APIView):
    """Эндпоинт выдает ссылку для привязки Telegram-аккаунта."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # создается новый токен или обновляется существующий для текущего пользователя
        binding, _ = TelegramBindingToken.objects.update_or_create(
            user=request.user,
            defaults={'token': uuid.uuid4(), 'created_at': timezone.now()}
        )
        
        bot_username = "salyk_bot"
        link = f"https://t.me/{bot_username}?start={binding.token}"
        
        return Response({"link": link})


class BotLinkConfirmView(APIView):
    """эндпоинт принимает код от бота и привязывает telegram_id к пользователю."""
    permission_classes = [IsTelegramBot]

    def post(self, request):
        token_str = request.data.get("code")
        tg_id = str(request.data.get("telegram_id"))
        
        binding = TelegramBindingToken.objects.filter(token=token_str).first()
        
        if not binding or binding.is_expired():
            return Response({"detail": "Код недействителен или просрочен"}, status=400)
            
        # Привязывает ID к пользователю и удаляет токен
        user = binding.user
        user.telegram_id = tg_id
        user.save()
        
        binding.delete()
        
        return Response({"status": "success", "email": user.email})


class BotAuthView(APIView):
    """эндпоинт для аутентификации бота по telegram_id и выдачи JWT-токенов."""
    permission_classes = [IsTelegramBot]

    def post(self, request):
        tg_id = str(request.data.get("telegram_id"))
        user = User.objects.filter(telegram_id=tg_id).first()
        
        if not user:
            return Response({"detail": "Пользователь не найден"}, status=404)
            
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })
