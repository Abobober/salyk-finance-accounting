from django.db import models
from django.conf import settings

from django.db import models
from django.conf import settings
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

    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NOT_STARTED
    )

    def __str__(self):
        return f"Organization of {self.user.email}"



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

