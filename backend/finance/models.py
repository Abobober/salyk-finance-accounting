from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import Q
from activities.models import ActivityCode
from organization.models import OrganizationActivity


class Category(models.Model):
    """Категории для доходов и расходов."""

    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Доход (категория)'
        EXPENSE = 'expense', 'Расход (категория)'

    name = models.CharField(max_length=100, verbose_name='Название категории')
    category_type = models.CharField(max_length=10, choices=CategoryType.choices, verbose_name='Тип категории')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    is_system = models.BooleanField(default=False, verbose_name='Системная категория')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_type_display()})"

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['category_type', 'name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name', 'category_type'], name='unique_category_per_user')
        ]


class Transaction(models.Model):
    """Финансовая операция с учетом бизнес-логики и налогов КР."""

    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Доход'
        EXPENSE = 'expense', 'Расход'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличный расчет'
        NON_CASH = 'non_cash', 'Безналичный расчет'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Пользователь'
    )

    # Связь с видом деятельности из онбординга
    activity_code = models.ForeignKey(
        ActivityCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Вид деятельности"
    )

    is_business = models.BooleanField(
        default=True,
        verbose_name="Относится к бизнесу?"
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        verbose_name='Метод оплаты'
    )

    # Учитывается ли в налоговой базе
    is_taxable = models.BooleanField(
        default=True,
        verbose_name="Учитывается в налоговой базе?"
    )

    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices, verbose_name='Тип операции')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Категория')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма'
    )

    description = models.TextField(blank=True, max_length=100, verbose_name='Описание')
    transaction_date = models.DateField(verbose_name='Дата операции')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    # Автоматически подтягиваем ставки из OrganizationActivity
    cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    non_cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_business and self.activity_code:
            try:
                org_activity = OrganizationActivity.objects.get(
                    profile=self.user.organization,
                    activity=self.activity_code
                )
                self.cash_tax_rate = org_activity.cash_tax_rate
                self.non_cash_tax_rate = org_activity.non_cash_tax_rate
            except OrganizationActivity.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} {self.amount} ({self.transaction_date})"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
        models.Index(fields=["user"]),
        models.Index(fields=["transaction_date"]),
        models.Index(fields=["created_at"]),
        models.Index(fields=["user", "transaction_date"]),
    ]

        constraints = [
        models.CheckConstraint(condition=Q(amount__gt=0), name="amount_positive"),
        models.CheckConstraint(condition=Q(amount__lte=1000000000), name="amount_reasonable_limit"),
    ]
