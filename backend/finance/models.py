from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Category(models.Model):
    """Категории для доходов и расходов."""

    class CategoryType(models.TextChoices):
        INCOME = 'income', 'Доход'
        EXPENSE = 'expense', 'Расход'

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
        constraints = [
            models.UniqueConstraint(fields=['user', 'name', 'category_type'], name='unique_category_per_user')
        ]


class Transaction(models.Model):
    """Финансовая операция (доход или расход)."""

    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Доход'
        EXPENSE = 'expense', 'Расход'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Пользователь'
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

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} {self.amount} ({self.transaction_date})"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['-transaction_date', 'user']),
        ]

    def clean(self) -> None:
        if self.category and self.category.category_type != self.transaction_type:
            raise ValidationError({
                'category': (
                    f"Категория '{self.category.name}' имеет тип '{self.category.category_type}', "
                    f"а операция имеет тип '{self.transaction_type}'"
                )
            })

    def save(self, *args, **kwargs):
        # ensure model-level validation runs on save
        self.full_clean()
        super().save(*args, **kwargs)