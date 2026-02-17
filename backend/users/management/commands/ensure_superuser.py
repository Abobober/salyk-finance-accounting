"""
Создаёт суперпользователя admin@gmail.com / admin, если его ещё нет.
Использование: python manage.py ensure_superuser
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEFAULT_EMAIL = 'admin@gmail.com'
DEFAULT_PASSWORD = 'admin'


class Command(BaseCommand):
    help = 'Создаёт суперпользователя admin@gmail.com / admin, если его ещё нет'

    def handle(self, *args, **options):
        if User.objects.filter(email=DEFAULT_EMAIL).exists():
            self.stdout.write(self.style.SUCCESS(f'Пользователь {DEFAULT_EMAIL} уже существует.'))
            return

        User.objects.create_superuser(email=DEFAULT_EMAIL, password=DEFAULT_PASSWORD)
        self.stdout.write(self.style.SUCCESS(f'Создан суперпользователь: {DEFAULT_EMAIL} / {DEFAULT_PASSWORD}'))
