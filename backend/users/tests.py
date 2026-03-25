from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


User = get_user_model()


class EnsureSuperuserCommandTests(TestCase):
    def test_command_skips_without_credentials(self):
        stdout = StringIO()

        call_command('ensure_superuser', stdout=stdout)

        self.assertEqual(User.objects.count(), 0)
        self.assertIn('superuser', stdout.getvalue().lower())

    def test_command_creates_superuser_from_args(self):
        stdout = StringIO()

        call_command(
            'ensure_superuser',
            email='admin@example.com',
            password='S3curePass123',
            stdout=stdout,
        )

        user = User.objects.get(email='admin@example.com')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
