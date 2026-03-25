from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from datetime import date

from finance.models import Category, Transaction


User = get_user_model()


class TransactionInvariantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='finance@example.com', password='StrongPass123')
        self.category = Category.objects.create(
            name='Office',
            category_type=Category.CategoryType.EXPENSE,
            user=self.user,
        )

    def test_business_transaction_requires_activity_code(self):
        transaction = Transaction(
            user=self.user,
            category=self.category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount='10.00',
            description='Office supplies',
            transaction_date=date(2026, 3, 25),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=None,
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_demo_data_command_creates_non_business_transactions_without_org_activities(self):
        call_command('setup_demo_data', user=self.user.email, transactions=5, skip_if_populated=False)

        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 5)
        self.assertFalse(Transaction.objects.filter(user=self.user, is_business=True).exists())
