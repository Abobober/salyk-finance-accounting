import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import TelegramBindingToken
from .permissions import IsTelegramBot
from .serializers import TgAuthSerializer, TgConfirmSerializer, TgLinkSerializer


User = get_user_model()


class GetTelegramLinkView(APIView):
    serializer_class = TgLinkSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        binding, _ = TelegramBindingToken.objects.update_or_create(
            user=request.user,
            defaults={'token': uuid.uuid4(), 'created_at': timezone.now()},
        )

        bot_username = getattr(settings, 'BOT_USERNAME', 'finance_iuca_bot')
        link = f"https://t.me/{bot_username}?start={binding.token}"
        return Response({"link": link})


class BotLinkConfirmView(APIView):
    serializer_class = TgConfirmSerializer
    permission_classes = [IsTelegramBot]

    def post(self, request):
        token_str = request.data.get("code")
        tg_id = str(request.data.get("telegram_id"))

        try:
            with transaction.atomic():
                binding = (
                    TelegramBindingToken.objects
                    .select_for_update()
                    .select_related("user")
                    .filter(token=token_str)
                    .first()
                )

                if not binding or binding.is_expired():
                    return Response({"detail": "Code is invalid or expired"}, status=400)

                if User.objects.select_for_update().filter(telegram_id=tg_id).exclude(pk=binding.user_id).exists():
                    return Response({"detail": "Telegram ID already linked to another user"}, status=409)

                user = binding.user
                user.telegram_id = tg_id
                user.save(update_fields=["telegram_id"])
                binding.delete()
        except IntegrityError:
            return Response({"detail": "Telegram ID already linked to another user"}, status=409)

        return Response({"status": "success", "email": user.email})


class BotAuthView(APIView):
    serializer_class = TgAuthSerializer
    permission_classes = [IsTelegramBot]

    def post(self, request):
        tg_id = str(request.data.get("telegram_id"))
        user = User.objects.filter(telegram_id=tg_id).first()

        if not user:
            return Response({"detail": "User not found"}, status=404)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
