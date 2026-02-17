import os

import requests
from organization.models import OrganizationProfile
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import os
from .serializers import ChatSessionSerializer
from .models import ChatSession
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "stepfun/step-3.5-flash:free"


class OpenRouterView(GenericAPIView):
    """
    AI-бухгалтер Кыргызстана с временной историей в RAM.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"
    serializer_class = ChatSessionSerializer

    def _build_user_org_context(self, request):
        context_parts = []
        user = request.user

        if not user or not user.is_authenticated:
            return context_parts

        context_parts.append(f"email пользователя: {user.email}")
        if getattr(user, "phone", None):
            context_parts.append(f"телефон пользователя: {user.phone}")

        try:
            profile = (
                OrganizationProfile.objects
                .select_related("user")
                .prefetch_related("activities__activity")
                .get(user=user)
            )
        except OrganizationProfile.DoesNotExist:
            return context_parts

        if profile.org_type:
            context_parts.append(f"тип организации: {profile.get_org_type_display()}")
        if profile.tax_regime:
            context_parts.append(f"налоговый режим: {profile.get_tax_regime_display()}")

        activities = profile.activities.all()
        if activities:
            activity_items = []
            for org_activity in activities:
                label = f"{org_activity.activity.code} - {org_activity.activity.name}"
                if org_activity.is_primary:
                    label += " (основной вид деятельности)"
                label += (
                    f", ставка наличные: {org_activity.cash_tax_rate}%, "
                    f"безналичные: {org_activity.non_cash_tax_rate}%"
                )
                activity_items.append(label)

            context_parts.append(
                "виды деятельности организации: " + "; ".join(activity_items)
            )

        return context_parts

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        session_id = serializer.validated_data["session_id"]

        session, _ = ChatSession.objects.get_or_create(
            session_id=session_id
        )  

        history = session.history

        # Формируем сообщения для модели
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты профессиональный бухгалтер Кыргызстана с опытом более 15 лет. "
                    "Специализируешься на ИП и ОсОО. Отлично знаешь налоговое законодательство КР, "
                    "ГНС, отчетность, Единый налог, НДС, подоходный налог, соцфонд, страховые взносы, "
                    "ЭСФ, ЭТТН и электронные сервисы налоговой. "
                    "Отвечай структурировано, профессионально и строго по законам КР. "
                    "Если данных недостаточно — задай уточняющий вопрос."
                )
            }
        ]

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        payload = {"model": MODEL_NAME, "messages": messages, "temperature": 0.2}
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return Response(
                {"error": "Ошибка запроса к OpenRouter", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            data = response.json()
            assistant_reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError):
            return Response(
                {"error": "Некорректный ответ от OpenRouter", "raw": data},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        session.append_message("user", message)
        session.append_message("assistant", assistant_reply)

        return Response(
            {"assistant": assistant_reply, "session_id": session_id},
            status=status.HTTP_200_OK,
        )
