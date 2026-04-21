from decimal import Decimal

from django.db.models import Case, DecimalField, Sum, Value, When
from django.db.models.functions import ExtractYear
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from config.openrouter import OpenRouterError, create_chat_completion
from finance.models import Transaction
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

    def _build_transactions_context(self, request):
        """Сводка транзакций пользователя для контекста модели (новые сверху)."""
        user = request.user
        if not user or not user.is_authenticated:
            return []

        totals_field = DecimalField(max_digits=18, decimal_places=2)
        base_qs = Transaction.objects.filter(user=user)

        totals = base_qs.aggregate(
            total_income=Sum(
                Case(
                    When(transaction_type=Transaction.TransactionType.INCOME, then="amount"),
                    default=Value(Decimal("0.00")),
                    output_field=totals_field,
                )
            ),
            total_expense=Sum(
                Case(
                    When(transaction_type=Transaction.TransactionType.EXPENSE, then="amount"),
                    default=Value(Decimal("0.00")),
                    output_field=totals_field,
                )
            ),
        )
        total_income = totals["total_income"] or Decimal("0.00")
        total_expense = totals["total_expense"] or Decimal("0.00")
        net_result = total_income - total_expense

        yearly_totals = (
            base_qs.annotate(year=ExtractYear("transaction_date"))
            .values("year")
            .annotate(
                total_income=Sum(
                    Case(
                        When(transaction_type=Transaction.TransactionType.INCOME, then="amount"),
                        default=Value(Decimal("0.00")),
                        output_field=totals_field,
                    )
                ),
                total_expense=Sum(
                    Case(
                        When(transaction_type=Transaction.TransactionType.EXPENSE, then="amount"),
                        default=Value(Decimal("0.00")),
                        output_field=totals_field,
                    )
                ),
            )
            .order_by("year")
        )

        max_rows = 500
        batch = list(
            base_qs
            .select_related("category", "activity_code")
            .order_by("-transaction_date", "-created_at")[: max_rows + 1]
        )
        if not batch:
            return []

        truncated = len(batch) > max_rows
        batch = batch[:max_rows]

        lines = []
        for t in batch:
            type_ru = "доход" if t.transaction_type == Transaction.TransactionType.INCOME else "расход"
            pay_ru = "наличные" if t.payment_method == Transaction.PaymentMethod.CASH else "безналичные"
            cat = t.category.name if t.category else "—"
            desc = (t.description or "—").strip() or "—"
            if t.activity_code:
                act = f"{t.activity_code.code} — {t.activity_code.name}"
            else:
                act = "—"
            lines.append(
                f"{t.transaction_date} | {type_ru} | {t.amount} KGS (сом) | {pay_ru} | "
                f"категория: {cat} | {desc} | "
                f"бизнес: {'да' if t.is_business else 'нет'} | "
                f"налогооблагаемая: {'да' if t.is_taxable else 'нет'} | ВД: {act}"
            )

        summary = (
            f"агрегаты по всем транзакциям пользователя: "
            f"итого доходов = {total_income} KGS (сом); "
            f"итого расходов = {total_expense} KGS (сом); "
            f"разница (доходы - расходы) = {net_result} KGS (сом)"
        )
        year_lines = []
        for row in yearly_totals:
            year = row["year"]
            year_income = row["total_income"] or Decimal("0.00")
            year_expense = row["total_expense"] or Decimal("0.00")
            year_net = year_income - year_expense
            year_lines.append(
                f"{year}: доходы = {year_income} KGS (сом); "
                f"расходы = {year_expense} KGS (сом); "
                f"разница = {year_net} KGS (сом)"
            )
        yearly_summary = "агрегаты по годам:\n" + "\n".join(year_lines)

        header = "транзакции пользователя (от новых к старым)"
        if truncated:
            header += f", показаны последние {max_rows} записей"
        return [summary, yearly_summary, header + ":\n" + "\n".join(lines)]

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
                    "KGS, сом и сомы - это одна и та же валюта: кыргызский сом. "
                    "Для вопросов за конкретный год используй именно строку этого года из блока 'агрегаты по годам'. "
                    "Не подставляй общие итоги вместо годовых и не пересчитывай вручную, если агрегат уже передан. "
                    "При расчетах по транзакциям считай суммы строго по переданному списку: "
                    "итог доходов = сумма строк с типом 'доход', итог расходов = сумма строк с типом 'расход', "
                    "чистый результат = доходы - расходы. "
                    "Если данных недостаточно, задай уточняющий вопрос."
                ),
            }
        ]

        user_context = self._build_user_org_context(request)
        user_context.extend(self._build_transactions_context(request))
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
