from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    Наследуемся от AbstractUser, чтобы получить все стандартные поля
    (username, email, password, first_name, last_name, etc.)
    """

    # поле для связи с Telegram-ботом
    telegram_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name="ID в Telegram"
    )
    
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    # phone_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'