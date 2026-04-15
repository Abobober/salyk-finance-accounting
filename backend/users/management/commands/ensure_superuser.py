import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

EMAIL_ENV_VAR = 'DJANGO_SUPERUSER_EMAIL'
PASSWORD_ENV_VAR = 'DJANGO_SUPERUSER_PASSWORD'


class Command(BaseCommand):
    help = 'Create a superuser from CLI args or env vars when credentials are provided'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')

    def handle(self, *args, **options):
        email = options.get('email') or os.getenv(EMAIL_ENV_VAR)
        password = options.get('password') or os.getenv(PASSWORD_ENV_VAR)

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    f'Skipping superuser creation. Provide --email/--password or env vars '
                    f'{EMAIL_ENV_VAR}/{PASSWORD_ENV_VAR}.'
                )
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'User {email} already exists.'))
            return

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {email}'))
