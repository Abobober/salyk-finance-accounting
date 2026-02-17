import os

import requests
from organization.models import OrganizationProfile
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .chat_sessions import append_history, get_history
from .serializers import ChatSessionSerializer

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "stepfun/step-3.5-flash:free"


class OpenRouterView(GenericAPIView):
    """
    AI-бухгалтер Кыргызстана с временной историей в RAM.
    """

    permission_classes = [AllowAny]
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
        user_context = serializer.validated_data.get("user_context")
        organization_context = serializer.validated_data.get("organization_context")

        history = get_history(session_id)

        prompt_context = self._build_user_org_context(request)
        if user_context:
            prompt_context.append(f"дополнительные данные пользователя: {user_context}")
        if organization_context:
            prompt_context.append(
                f"дополнительные данные организации: {organization_context}"
            )

        system_prompt = (
            "Ты профессиональный бухгалтер Кыргызстана с опытом более 15 лет. "
            "Специализируешься на ИП и ОсОО. Отлично знаешь налоговое законодательство КР, "
            "ГНС, отчетность, Единый налог, НДС, подоходный налог, соцфонд, страховые взносы, "
            "ЭСФ, ЭТТН и электронные сервисы налоговой. "
            "Отвечай структурировано, профессионально и строго по законам КР. "
            "Давай рекомендации с учетом данных пользователя, организации и вида деятельности, если они переданы. "
            "Если данных недостаточно - задай уточняющий вопрос."
        )
        if prompt_context:
            system_prompt += "\n\nКонтекст клиента:\n- " + "\n- ".join(prompt_context)

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

        append_history(session_id, "user", message)
        append_history(session_id, "assistant", assistant_reply)

        return Response(
            {"assistant": assistant_reply, "session_id": session_id},
            status=status.HTTP_200_OK,
        )
