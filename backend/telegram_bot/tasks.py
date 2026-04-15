from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from telegram_bot.models import TelegramBindingToken


@shared_task
def cleanup_expired_binding_tokens():
    threshold = timezone.now() - timedelta(minutes=10)
    deleted_count, _ = TelegramBindingToken.objects.filter(created_at__lt=threshold).delete()
    return deleted_count
