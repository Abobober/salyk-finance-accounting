from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from users.models import ActivityCode


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

    # Учитывается ли в налоговой базе (для доходов - облагаемый, для расходов - учитываемый)
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

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} {self.amount} ({self.transaction_date})"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['-transaction_date', 'user', 'is_business']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)