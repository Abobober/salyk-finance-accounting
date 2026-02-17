from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from activities.models import ActivityCode


class OrganizationProfile(models.Model):
    """
    Модель для хранения информации о налоговом режиме и видах деятельности пользователя.
    """
    class OrgType(models.TextChoices):
        IE = 'ie', 'ИП'
        LLC = 'llc', 'ОсОО'

    class TaxRegime(models.TextChoices):
        SINGLE = 'single', 'Единый налог'
        GENERAL = 'general', 'Общий налоговый режим'

    class TaxPeriodType(models.TextChoices):
        PRESET = 'preset', 'Предустановленный период'
        CUSTOM = 'custom', 'Пользовательский период'

    class TaxPeriodPreset(models.TextChoices):
        MONTHLY = 'monthly', 'Ежемесячно (1-е число)'
        QUARTERLY = 'quarterly', 'Ежеквартально (1-е число)'
        YEARLY = 'yearly', 'Ежегодно (1 января)'

    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'not_started'
        ORG_TYPE = 'org_type'
        TAX_REGIME = 'tax_regime'
        ACTIVITIES = 'activities'
        COMPLETED = 'completed'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization'
    )

    org_type = models.CharField(max_length=10, choices=OrgType.choices, null=True, blank=True)
    tax_regime = models.CharField(max_length=15, choices=TaxRegime.choices, null=True, blank=True)

    # Tax period settings
    tax_period_type = models.CharField(
        max_length=10,
        choices=TaxPeriodType.choices,
        null=True,
        blank=True,
        verbose_name='Тип налогового периода'
    )
    tax_period_preset = models.CharField(
        max_length=15,
        choices=TaxPeriodPreset.choices,
        null=True,
        blank=True,
        verbose_name='Предустановленный налоговый период'
    )
    tax_period_custom_day = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name='День месяца для пользовательского периода (1-31)'
    )

    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NOT_STARTED
    )

    def __str__(self):
        return f"Organization of {self.user.email}"

    def clean(self):
        """Validate tax period settings."""
        if self.tax_period_type == self.TaxPeriodType.PRESET and not self.tax_period_preset:
            raise ValidationError({
                'tax_period_preset': 'Необходимо выбрать предустановленный период.'
            })
        if self.tax_period_type == self.TaxPeriodType.CUSTOM and not self.tax_period_custom_day:
            raise ValidationError({
                'tax_period_custom_day': 'Необходимо указать день месяца для пользовательского периода.'
            })
        if self.tax_period_type == self.TaxPeriodType.PRESET and self.tax_period_custom_day:
            raise ValidationError({
                'tax_period_custom_day': 'День месяца не используется для предустановленного периода.'
            })
        if self.tax_period_type == self.TaxPeriodType.CUSTOM and self.tax_period_preset:
            raise ValidationError({
                'tax_period_preset': 'Предустановленный период не используется для пользовательского типа.'
            })



class OrganizationActivity(models.Model):
    """
    Промежуточная модель для связи профиля организации с видами деятельности.
    """
    profile = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity = models.ForeignKey(ActivityCode, on_delete=models.PROTECT)

    cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    non_cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)

    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'activity')

