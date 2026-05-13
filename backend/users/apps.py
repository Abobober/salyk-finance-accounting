from django.apps import AppConfig
from django.contrib import admin


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Управление пользователями'

    def ready(self):
        # JWT blacklist в админке путает поддержку и часто ломает навигацию; токены не правят руками.
        try:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

            for model in (OutstandingToken, BlacklistedToken):
                if admin.site.is_registered(model):
                    admin.site.unregister(model)
        except Exception:
            pass
