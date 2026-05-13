from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from activities.models import ActivityCode


class OrganizationProfile(models.Model):
    class OrgType(models.TextChoices):
        IE = 'ie', 'IE'
        LLC = 'llc', 'LLC'

    class TaxRegime(models.TextChoices):
        SINGLE = 'single', 'Single tax'
        GENERAL = 'general', 'General tax regime'

    class TaxPeriodType(models.TextChoices):
        PRESET = 'preset', 'Preset period'
        CUSTOM = 'custom', 'Custom period'

    class TaxPeriodPreset(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        YEARLY = 'yearly', 'Yearly'

    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        ORG_TYPE = 'org_type', 'Organization type'
        TAX_REGIME = 'tax_regime', 'Tax regime'
        ACTIVITIES = 'activities', 'Activities'
        COMPLETED = 'completed', 'Completed'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization',
    )
    org_type = models.CharField(max_length=10, choices=OrgType.choices, null=True, blank=True)
    tax_regime = models.CharField(max_length=15, choices=TaxRegime.choices, null=True, blank=True)
    tin = models.CharField(max_length=30, null=True, blank=True)
    taxpayer_name = models.CharField(max_length=255, null=True, blank=True)
    tax_office_code = models.CharField(max_length=50, null=True, blank=True)
    tax_office_name = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    tax_period_type = models.CharField(max_length=10, choices=TaxPeriodType.choices, null=True, blank=True)
    tax_period_preset = models.CharField(max_length=15, choices=TaxPeriodPreset.choices, null=True, blank=True)
    tax_period_custom_day = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    inn = models.CharField(max_length=20, null=True, blank=True)
    tax_authority_code = models.CharField(max_length=30, null=True, blank=True)
    tax_authority_name = models.CharField(max_length=255, null=True, blank=True)
    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NOT_STARTED,
    )

    def __str__(self):
        return f'Organization of {self.user.email}'

    def clean(self):
        if not self.tax_period_type:
            if self.tax_period_preset or self.tax_period_custom_day is not None:
                raise ValidationError({
                    'tax_period_type': 'Choose a tax period type before filling its settings.',
                })
            return

        if self.tax_period_type == self.TaxPeriodType.PRESET and not self.tax_period_preset:
            raise ValidationError({
                'tax_period_preset': 'Preset tax period is required.',
            })

        if self.tax_period_type == self.TaxPeriodType.CUSTOM and not self.tax_period_custom_day:
            raise ValidationError({
                'tax_period_custom_day': 'Custom day is required for custom periods.',
            })

        if self.tax_period_type == self.TaxPeriodType.CUSTOM and self.tax_period_preset:
            raise ValidationError({
                'tax_period_preset': 'Preset period must be empty for custom periods.',
            })

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(tax_period_type__isnull=True) &
                     models.Q(tax_period_preset__isnull=True) &
                     models.Q(tax_period_custom_day__isnull=True)) |
                    (models.Q(tax_period_type='preset') &
                     models.Q(tax_period_preset__isnull=False)) |
                    (models.Q(tax_period_type='custom') &
                     models.Q(tax_period_custom_day__isnull=False) &
                     models.Q(tax_period_preset__isnull=True))
                ),
                name='organization_tax_period_state_valid',
            ),
        ]


class OrganizationActivity(models.Model):
    profile = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    activity = models.ForeignKey(ActivityCode, on_delete=models.PROTECT)
    cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    non_cash_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['profile', 'activity'], name='unique_profile_activity'),
            models.UniqueConstraint(
                fields=['profile'],
                condition=models.Q(is_primary=True),
                name='unique_primary_activity_per_profile',
            ),
        ]
