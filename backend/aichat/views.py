from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from config.openrouter import OpenRouterError, create_chat_completion
from organization.models import OrganizationProfile

from .models import ChatSession
from .serializers import ChatSessionSerializer


class OpenRouterView(GenericAPIView):
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

        session, _ = ChatSession.objects.get_or_create(session_id=session_id)
        history = session.history

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты профессиональный бухгалтер Кыргызстана с опытом более 15 лет. "
                    "Специализируешься на ИП и ОсОО. Отлично знаешь налоговое законодательство КР, "
                    "ГНС, отчетность, Единый налог, НДС, подоходный налог, соцфонд, страховые взносы, "
                    "ЭСФ, ЭТТН и электронные сервисы налоговой. "
                    "Отвечай структурированно, профессионально и строго по законам КР. "
                    "Если данных недостаточно, задай уточняющий вопрос."
                ),
            }
        ]

        user_context = self._build_user_org_context(request)
        if user_context:
            messages[0]["content"] += "\n\nКонтекст: " + "; ".join(user_context)

        messages.extend(history)
        messages.append({"role": "user", "content": message})

        try:
            assistant_reply = create_chat_completion(
                messages=messages,
                temperature=0.2,
                timeout=60,
            )
        except OpenRouterError as exc:
            return Response({"error": exc.message}, status=exc.status_code)

        session.append_message("user", message)
        session.append_message("assistant", assistant_reply)

        return Response(
            {"assistant": assistant_reply, "session_id": session_id},
            status=status.HTTP_200_OK,
        )
