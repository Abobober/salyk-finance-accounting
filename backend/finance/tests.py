from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from datetime import date
from unittest.mock import patch

from finance.cache_utils import get_finance_cache_version
from finance.models import Category, Transaction
from finance.services.dashboard_service import get_dashboard_data


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

    def test_dashboard_payload_uses_cache_between_identical_requests(self):
        with self.captureOnCommitCallbacks(execute=True):
            Transaction.objects.create(
                user=self.user,
                category=self.category,
                transaction_type=Transaction.TransactionType.EXPENSE,
                amount='10.00',
                description='Cached dashboard',
                transaction_date=date(2026, 3, 25),
                payment_method=Transaction.PaymentMethod.CASH,
                is_business=False,
                is_taxable=True,
            )

        with patch('finance.services.dashboard_service._build_dashboard_data', wraps=get_dashboard_data.__globals__['_build_dashboard_data']) as builder:
            get_dashboard_data(self.user, filters={})
            get_dashboard_data(self.user, filters={})

        self.assertEqual(builder.call_count, 1)

    def test_transaction_change_bumps_finance_cache_version(self):
        version_before = get_finance_cache_version(self.user.id)

        with self.captureOnCommitCallbacks(execute=True):
            Transaction.objects.create(
                user=self.user,
                category=self.category,
                transaction_type=Transaction.TransactionType.EXPENSE,
                amount='15.00',
                description='Invalidate cache',
                transaction_date=date(2026, 3, 25),
                payment_method=Transaction.PaymentMethod.CASH,
                is_business=False,
                is_taxable=True,
            )

        version_after = get_finance_cache_version(self.user.id)
        self.assertGreater(version_after, version_before)
