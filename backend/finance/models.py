from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from activities.models import ActivityCode
from organization.models import OrganizationActivity

from .constants import MAX_TRANSACTION_AMOUNT, MIN_TRANSACTION_AMOUNT
from .managers import ActiveTransactionManager


class Category(models.Model):
    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CategoryType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_type_display()})"

    class Meta:
        verbose_name_plural = "Категории"
        ordering = ['category_type', 'name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name', 'category_type'], name='unique_category_per_user')
        ]


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        NON_CASH = 'non_cash', 'Non-cash'

    objects = ActiveTransactionManager()
    all_objects = models.Manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    activity_code = models.ForeignKey(
        ActivityCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_business = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    is_taxable = models.BooleanField(default=True)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(MIN_TRANSACTION_AMOUNT)],
    )
    description = models.TextField(blank=True, max_length=100)
    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    non_cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Дата удаления',
        help_text='Запись скрыта из API и отчётов, но хранится в БД.',
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_transactions',
        verbose_name='Последнее изменение'
    )

    def clean(self):
        if self.is_business and not self.activity_code:
            raise ValidationError({
                'activity_code': 'Business transactions require an activity code.',
            })

    def save(self, *args, **kwargs):
        if self.is_business and self.activity_code:
            org_activity = (
                OrganizationActivity.objects
                .filter(profile__user=self.user, activity=self.activity_code)
                .first()
            )
            if org_activity:
                self.cash_tax_rate = org_activity.cash_tax_rate
                self.non_cash_tax_rate = org_activity.non_cash_tax_rate
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} {self.amount} ({self.transaction_date})"

    class Meta:
        verbose_name_plural = "Транзакции"
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["user", "deleted_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=MIN_TRANSACTION_AMOUNT),
                name="amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(amount__lte=MAX_TRANSACTION_AMOUNT),
                name="amount_reasonable_limit",
            ),
            models.CheckConstraint(
                condition=Q(is_business=False) | Q(activity_code__isnull=False),
                name="business_transaction_requires_activity_code",
            ),
        ]


class TransactionLog(models.Model):
    """Журнал действий с транзакцией"""

    class Action(models.TextChoices):
        CREATED = 'created', 'Создание'
        SOFT_DELETED = 'soft_deleted', 'Удаление (в корзину)'
        RESTORED = 'restored', 'Восстановление'

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Транзакция',
    )
    action = models.CharField(max_length=20, choices=Action.choices, verbose_name='Действие')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction_log_entries',
        verbose_name='Кто выполнил',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Когда')
    note = models.CharField(max_length=255, blank=True, verbose_name='Заметка')

    class Meta:
        verbose_name = 'Запись журнала транзакции'
        verbose_name_plural = 'Журнал транзакций'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.get_action_display()} #{self.transaction_id}'
