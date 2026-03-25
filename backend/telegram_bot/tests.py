from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from telegram_bot.models import TelegramBindingToken
from telegram_bot.tasks import cleanup_expired_binding_tokens


User = get_user_model()


class TelegramTasksTests(TestCase):
    def test_cleanup_expired_binding_tokens_removes_old_records(self):
        user = User.objects.create_user(email='tg@example.com', password='StrongPass123')
        token = TelegramBindingToken.objects.create(user=user)
        TelegramBindingToken.objects.filter(pk=token.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )

        deleted_count = cleanup_expired_binding_tokens()

        self.assertEqual(deleted_count, 1)
        self.assertFalse(TelegramBindingToken.objects.filter(pk=token.pk).exists())
