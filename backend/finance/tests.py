from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from activities.models import ActivityCode
from finance.cache_utils import get_finance_cache_version
from finance.models import Category, Transaction, TransactionLog
from finance.services.dashboard_service import get_dashboard_data
from finance.services.transaction_service import TransactionService
from organization.models import OrganizationActivity, OrganizationProfile
from rest_framework.test import APIClient


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


class TransactionSoftDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='softdel@example.com', password='StrongPass123')
        self.category = Category.objects.create(
            name='Misc',
            category_type=Category.CategoryType.EXPENSE,
            user=self.user,
        )

    def _validated_new_tx(self):
        return {
            'category': self.category,
            'transaction_type': Transaction.TransactionType.EXPENSE,
            'amount': Decimal('10.00'),
            'description': 'coffee',
            'transaction_date': date(2026, 4, 1),
            'payment_method': Transaction.PaymentMethod.CASH,
            'is_business': False,
            'is_taxable': True,
            'activity_code': None,
        }

    def test_soft_delete_restore_and_logs(self):
        tx = TransactionService.create_transaction(self.user, self._validated_new_tx())
        self.assertEqual(
            list(TransactionLog.objects.filter(transaction=tx).values_list('action', flat=True)),
            [TransactionLog.Action.CREATED],
        )

        TransactionService.soft_delete(tx, self.user)
        self.assertFalse(Transaction.objects.filter(pk=tx.pk).exists())
        self.assertIsNotNone(Transaction.all_objects.get(pk=tx.pk).deleted_at)
        self.assertEqual(
            list(TransactionLog.objects.filter(transaction=tx).values_list('action', flat=True)),
            [TransactionLog.Action.SOFT_DELETED, TransactionLog.Action.CREATED],
        )

        TransactionService.restore_transaction(Transaction.all_objects.get(pk=tx.pk), self.user)
        self.assertTrue(Transaction.objects.filter(pk=tx.pk).exists())
        self.assertIsNone(Transaction.objects.get(pk=tx.pk).deleted_at)
        actions = set(TransactionLog.objects.filter(transaction=tx).values_list('action', flat=True))
        self.assertEqual(
            actions,
            {
                TransactionLog.Action.CREATED,
                TransactionLog.Action.SOFT_DELETED,
                TransactionLog.Action.RESTORED,
            },
        )


class TaxReportV2ApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(email='report@example.com', password='StrongPass123')
        self.client.force_authenticate(self.user)

        self.profile = OrganizationProfile.objects.create(
            user=self.user,
            org_type=OrganizationProfile.OrgType.IE,
            tax_regime=OrganizationProfile.TaxRegime.SINGLE,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.MONTHLY,
            onboarding_status=OrganizationProfile.OnboardingStatus.COMPLETED,
        )
        self.primary_activity = ActivityCode.objects.create(code='A01', section='A', name='Primary activity')
        self.secondary_activity = ActivityCode.objects.create(code='B02', section='B', name='Secondary activity')
        self.unlinked_activity = ActivityCode.objects.create(code='C03', section='C', name='Unlinked activity')

        self.primary_org_activity = OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.primary_activity,
            cash_tax_rate=Decimal('3.00'),
            non_cash_tax_rate=Decimal('2.00'),
            is_primary=True,
        )
        self.secondary_org_activity = OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.secondary_activity,
            cash_tax_rate=Decimal('4.00'),
            non_cash_tax_rate=Decimal('5.00'),
            is_primary=False,
        )

        self.income_category = Category.objects.create(
            name='Sales',
            category_type=Category.CategoryType.INCOME,
            user=self.user,
        )
        self.expense_category = Category.objects.create(
            name='Office',
            category_type=Category.CategoryType.EXPENSE,
            user=self.user,
        )

    def _report(self, query: str):
        return self.client.get(f'/api/finance/tax-report/v2/{query}')

    def _create_transaction(
        self,
        *,
        amount: str,
        transaction_type: str,
        transaction_date: date,
        payment_method: str,
        is_business: bool,
        is_taxable: bool,
        activity_code=None,
        category=None,
        description='tx',
    ):
        if category is None:
            category = self.income_category if transaction_type == Transaction.TransactionType.INCOME else self.expense_category

        return Transaction.objects.create(
            user=self.user,
            category=category,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            transaction_date=transaction_date,
            payment_method=payment_method,
            is_business=is_business,
            is_taxable=is_taxable,
            activity_code=activity_code,
        )

    def test_v2_report_returns_expected_summary_breakdowns_and_warnings(self):
        self._create_transaction(
            amount='100.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 10),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='cash income',
        )
        self._create_transaction(
            amount='200.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 11),
            payment_method=Transaction.PaymentMethod.NON_CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.secondary_activity,
            description='non cash income',
        )
        self._create_transaction(
            amount='50.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 12),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=False,
            activity_code=self.primary_activity,
            description='non taxable income',
        )
        self._create_transaction(
            amount='40.00',
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date=date(2026, 3, 13),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='taxable expense',
        )
        self._create_transaction(
            amount='10.00',
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date=date(2026, 3, 14),
            payment_method=Transaction.PaymentMethod.NON_CASH,
            is_business=False,
            is_taxable=False,
            description='non taxable expense',
        )
        self._create_transaction(
            amount='30.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 15),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=False,
            is_taxable=True,
            description='taxable non-business income',
        )

        response = self._report('?date_from=2026-03-01&date_to=2026-03-31')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['schema_version'], '2.0')
        self.assertEqual(response.data['meta']['currency'], 'KGS')
        self.assertEqual(response.data['summary'], {
            'transaction_count': 6,
            'total_income': '380.00',
            'total_expense': '50.00',
            'net': '330.00',
            'taxable_income': '330.00',
            'taxable_expense': '40.00',
            'non_taxable_income': '50.00',
            'non_taxable_expense': '10.00',
            'total_tax_due': '13.00',
        })

        by_payment_method = {row['payment_method']: row for row in response.data['breakdowns']['by_payment_method']}
        self.assertEqual(by_payment_method['cash'], {
            'payment_method': 'cash',
            'payment_method_display': 'Cash',
            'income': '180.00',
            'expense': '40.00',
            'taxable_income': '130.00',
            'taxable_expense': '40.00',
            'net': '140.00',
            'tax_due': '3.00',
        })
        self.assertEqual(by_payment_method['non_cash'], {
            'payment_method': 'non_cash',
            'payment_method_display': 'Non-cash',
            'income': '200.00',
            'expense': '10.00',
            'taxable_income': '200.00',
            'taxable_expense': '0.00',
            'net': '190.00',
            'tax_due': '10.00',
        })

        by_activity = {row['activity_code']: row for row in response.data['breakdowns']['by_activity']}
        self.assertEqual(by_activity['A01'], {
            'activity_code_id': self.primary_activity.id,
            'activity_code': 'A01',
            'activity_name': 'Primary activity',
            'is_primary': True,
            'income': '150.00',
            'expense': '40.00',
            'taxable_income': '100.00',
            'taxable_expense': '40.00',
            'net': '110.00',
            'tax_due': '3.00',
        })
        self.assertEqual(by_activity['B02'], {
            'activity_code_id': self.secondary_activity.id,
            'activity_code': 'B02',
            'activity_name': 'Secondary activity',
            'is_primary': False,
            'income': '200.00',
            'expense': '0.00',
            'taxable_income': '200.00',
            'taxable_expense': '0.00',
            'net': '200.00',
            'tax_due': '10.00',
        })

        self.assertEqual(response.data['tax_calculation']['items'], [
            {
                'activity_code_id': self.primary_activity.id,
                'activity_code': 'A01',
                'activity_name': 'Primary activity',
                'payment_method': 'cash',
                'payment_method_display': 'Cash',
                'applied_rate': '3.00',
                'rate_source': 'transaction_snapshot',
                'taxable_base': '100.00',
                'transaction_count': 1,
                'tax_due': '3.00',
            },
            {
                'activity_code_id': self.secondary_activity.id,
                'activity_code': 'B02',
                'activity_name': 'Secondary activity',
                'payment_method': 'non_cash',
                'payment_method_display': 'Non-cash',
                'applied_rate': '5.00',
                'rate_source': 'transaction_snapshot',
                'taxable_base': '200.00',
                'transaction_count': 1,
                'tax_due': '10.00',
            },
        ])
        self.assertEqual(response.data['warnings'], [
            {
                'code': 'non_business_taxable_income_excluded',
                'message': 'Taxable non-business income was excluded from tax_due.',
                'count': 1,
            }
        ])

    def test_v2_report_empty_period_returns_zero_safe_payload(self):
        response = self._report('?date_from=2026-03-01&date_to=2026-03-31')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary'], {
            'transaction_count': 0,
            'total_income': '0.00',
            'total_expense': '0.00',
            'net': '0.00',
            'taxable_income': '0.00',
            'taxable_expense': '0.00',
            'non_taxable_income': '0.00',
            'non_taxable_expense': '0.00',
            'total_tax_due': '0.00',
        })
        self.assertEqual(len(response.data['breakdowns']['by_payment_method']), 2)
        self.assertEqual(response.data['breakdowns']['by_activity'], [])
        self.assertEqual(response.data['tax_calculation']['items'], [])
        self.assertEqual(response.data['warnings'], [])

    def test_v2_report_uses_organization_tax_period(self):
        self.profile.tax_period_custom_day = 20
        self.profile.save(update_fields=['tax_period_custom_day'])

        self._create_transaction(
            amount='100.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 21),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='inside org period',
        )
        self._create_transaction(
            amount='60.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 19),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='outside org period',
        )

        fixed_now = datetime(2026, 3, 25, 10, 0, tzinfo=timezone.get_current_timezone())
        with patch('organization.tax_period_utils.timezone.now', return_value=fixed_now):
            response = self._report('?use_org_tax_period=true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['period'], {
            'mode': 'org_tax_period',
            'preset': None,
            'date_from': '2026-03-20',
            'date_to': '2026-04-19',
        })
        self.assertEqual(response.data['summary']['transaction_count'], 1)
        self.assertEqual(response.data['summary']['total_income'], '100.00')

    def test_v2_report_requires_explicit_period_selector(self):
        response = self.client.get('/api/finance/tax-report/v2/')

        self.assertEqual(response.status_code, 400)
        self.assertIn('Provide exactly one period selector', response.data['error'])

    def test_v2_report_rejects_unsupported_filters(self):
        response = self._report('?preset=month&category=1')

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported query params', response.data['error'])

    def test_v2_report_uses_transaction_snapshot_rate_before_current_org_rate(self):
        self._create_transaction(
            amount='100.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 10),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='snapshot precedence',
        )
        self.primary_org_activity.cash_tax_rate = Decimal('9.00')
        self.primary_org_activity.save(update_fields=['cash_tax_rate'])

        response = self._report('?date_from=2026-03-01&date_to=2026-03-31')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_tax_due'], '3.00')
        self.assertEqual(response.data['tax_calculation']['items'][0]['applied_rate'], '3.00')
        self.assertEqual(response.data['tax_calculation']['items'][0]['rate_source'], 'transaction_snapshot')

    def test_v2_report_falls_back_to_current_org_activity_rate(self):
        transaction = self._create_transaction(
            amount='100.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 10),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.primary_activity,
            description='fallback rate',
        )
        Transaction.objects.filter(pk=transaction.pk).update(
            cash_tax_rate=None,
            non_cash_tax_rate=None,
        )

        response = self._report('?date_from=2026-03-01&date_to=2026-03-31')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_tax_due'], '3.00')
        self.assertEqual(response.data['tax_calculation']['items'][0]['applied_rate'], '3.00')
        self.assertEqual(response.data['tax_calculation']['items'][0]['rate_source'], 'organization_activity')

    def test_v2_report_excludes_taxable_business_income_without_any_rate(self):
        self._create_transaction(
            amount='120.00',
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date=date(2026, 3, 10),
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
            activity_code=self.unlinked_activity,
            description='missing rate',
        )

        response = self._report('?date_from=2026-03-01&date_to=2026-03-31')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['taxable_income'], '120.00')
        self.assertEqual(response.data['summary']['total_tax_due'], '0.00')
        self.assertEqual(response.data['tax_calculation']['items'], [])
        self.assertEqual(response.data['warnings'], [
            {
                'code': 'missing_tax_rate',
                'message': 'Taxable business income without any applicable tax rate was excluded from tax_due.',
                'count': 1,
            }
        ])

    def test_organization_activity_change_invalidates_finance_cache(self):
        version_before = get_finance_cache_version(self.user.id)

        with self.captureOnCommitCallbacks(execute=True):
            self.primary_org_activity.cash_tax_rate = Decimal('7.00')
            self.primary_org_activity.save(update_fields=['cash_tax_rate'])

        version_after = get_finance_cache_version(self.user.id)
        self.assertGreater(version_after, version_before)

    def test_organization_profile_change_invalidates_finance_cache(self):
        version_before = get_finance_cache_version(self.user.id)

        with self.captureOnCommitCallbacks(execute=True):
            self.profile.tax_period_custom_day = 12
            self.profile.save(update_fields=['tax_period_custom_day'])

        version_after = get_finance_cache_version(self.user.id)
        self.assertGreater(version_after, version_before)
