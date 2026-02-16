import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class TelegramBindingToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='tg_binding_token'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Токен живет 10 минут
        return (timezone.now() - self.created_at).total_seconds() > 600

    def __str__(self):
        return f"Token for {self.user.email}"
