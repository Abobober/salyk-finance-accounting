from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUserManager(BaseUserManager):
    """Менеджер пользователей, использующий email как логин."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя без `username`, авторизация по `email`."""

    username = None
    email = models.EmailField('email address', unique=True)

    # поле для связи с Telegram-ботом
    telegram_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name="ID в Telegram"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f"{self.email}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ActivityCode(models.Model):
    """Справочник ГКЭД (ОКЭД) Кыргызстана."""
    code = models.CharField(max_length=20, unique=True, verbose_name="Код (ГКЭД)")
    section = models.CharField(max_length=5, verbose_name="Секция")
    name = models.TextField(verbose_name="Наименование деятельности")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Вид деятельности"
        verbose_name_plural = "Виды деятельности"

class OrganizationProfile(models.Model):
    """Налоговый профиль пользователя (ИП/ОсОО)."""
    class OrgType(models.TextChoices):
        IE = 'ie', 'ИП (Индивидуальный предприниматель)'
        LLC = 'llc', 'ОсОО (Общество с ограниченной ответственностью)'

    class TaxRegime(models.TextChoices):
        GENERAL = 'general', 'Общий налоговый режим'
        SINGLE = 'single', 'Единый налог'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    org_type = models.CharField(max_length=10, choices=OrgType.choices)
    tax_regime = models.CharField(max_length=15, choices=TaxRegime.choices)
    
    # Виды деятельности
    primary_activity = models.ForeignKey(ActivityCode, on_delete=models.PROTECT, related_name='primary_for')
    additional_activities = models.ManyToManyField(ActivityCode, blank=True, related_name='secondary_for')

    # Ставки налогов (вводятся вручную пользователем)
    cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Ставка (наличные, %)")
    non_cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Ставка (безнал, %)")

    is_onboarded = models.BooleanField(default=False)