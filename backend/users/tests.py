from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


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


class IdempotencyMiddlewareTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'duplicate@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_registration_request_is_replayed_with_same_idempotency_key(self):
        response1 = self.client.post(
            '/api/users/register/',
            self.payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='reg-1',
        )
        response2 = self.client.post(
            '/api/users/register/',
            self.payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='reg-1',
        )

        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(User.objects.filter(email='duplicate@example.com').count(), 1)
        self.assertEqual(response2['X-Idempotent-Replay'], 'true')

    def test_registration_request_rejects_same_key_with_different_body(self):
        self.client.post(
            '/api/users/register/',
            self.payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY='reg-2',
        )
        response = self.client.post(
            '/api/users/register/',
            {
                **self.payload,
                'email': 'another@example.com',
            },
            format='json',
            HTTP_IDEMPOTENCY_KEY='reg-2',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.objects.filter(email='another@example.com').count(), 0)
