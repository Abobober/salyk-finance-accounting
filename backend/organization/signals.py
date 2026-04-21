from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from finance.cache_utils import invalidate_finance_cache_on_commit
from organization.models import OrganizationActivity, OrganizationProfile


@receiver(post_save, sender=OrganizationProfile)
@receiver(post_delete, sender=OrganizationProfile)
def invalidate_finance_cache_for_profile(sender, instance, **kwargs):
    invalidate_finance_cache_on_commit(instance.user_id)


@receiver(post_save, sender=OrganizationActivity)
@receiver(post_delete, sender=OrganizationActivity)
def invalidate_finance_cache_for_activity(sender, instance, **kwargs):
    invalidate_finance_cache_on_commit(instance.profile.user_id)
