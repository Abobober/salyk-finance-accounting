from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from finance.cache_utils import invalidate_finance_cache_on_commit
from finance.models import Category, Transaction


@receiver(post_save, sender=Transaction)
@receiver(post_delete, sender=Transaction)
def invalidate_transaction_related_cache(sender, instance, **kwargs):
    invalidate_finance_cache_on_commit(instance.user_id)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_related_cache(sender, instance, **kwargs):
    if instance.user_id:
        invalidate_finance_cache_on_commit(instance.user_id)
