from rest_framework import permissions
from django.conf import settings

class IsTelegramBot(permissions.BasePermission):
    """Проверяет, что запрос приходит от  бота, используя секретный ключ в заголовке."""
    def has_permission(self, request, view):
        bot_secret = request.headers.get('X-Bot-Secret')
        return bot_secret == getattr(settings, 'BOT_API_SECRET', None)
