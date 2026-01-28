from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Category(models.Model):
    """
    Категории для доходов и расходов.
    Примеры: 'Продукты', 'Транспорт', 'Зарплата', 'Услуги'
    """
    
    # Типы категорий
    INCOME = 'income'
    EXPENSE = 'expense'
    CATEGORY_TYPES = [
        (INCOME, 'Доход'),
        (EXPENSE, 'Расход'),
    ]
    
    name = models.CharField(
        max_length=100, 
        verbose_name='Название категории'
    )
    
    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPES,
        verbose_name='Тип категории'
    )
    
    # Пользователь, который создал категорию (если None - системная категория)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    # Является ли категория системной (по умолчанию)
    is_system = models.BooleanField(
        default=False,
        verbose_name='Системная категория'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        # Ограничение: у одного пользователя не может быть двух категорий с одинаковым именем
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'category_type'],
                name='unique_category_per_user'
            )
        ]


class Transaction(models.Model):
    """
    Финансовая операция (доход или расход).
    Это самая важная модель в приложении.
    """
    
    # Типы операций
    INCOME = 'income'
    EXPENSE = 'expense'
    TRANSACTION_TYPES = [
        (INCOME, 'Доход'),
        (EXPENSE, 'Расход'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Пользователь'
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        verbose_name='Тип операции'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Сумма'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    transaction_date = models.DateField(
        verbose_name='Дата операции'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания записи'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} ({self.transaction_date})"
    
    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-transaction_date', '-created_at']
    
    def save(self, *args, **kwargs):
        """
        При сохранении проверяем, что категория соответствует типу операции.
        """
        if self.category and self.category.category_type != self.transaction_type:
            raise ValueError(
                f"Категория '{self.category.name}' имеет тип '{self.category.category_type}', "
                f"а операция имеет тип '{self.transaction_type}'"
            )
        super().save(*args, **kwargs)