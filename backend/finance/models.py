from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from activities.models import ActivityCode
from organization.models import OrganizationActivity

from .constants import MAX_TRANSACTION_AMOUNT, MIN_TRANSACTION_AMOUNT


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
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "transaction_date"]),
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
