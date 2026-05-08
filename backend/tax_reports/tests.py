from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from activities.models import ActivityCode
from finance.models import Category, Transaction
from organization.models import OrganizationActivity, OrganizationProfile
from tax_reports.services.report_data_builder import STI091ReportDataBuilder


User = get_user_model()


class STI091ReportDataBuilderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='sti091@example.com',
            password='StrongPass123',
            first_name='ИП',
            last_name='Тестов',
            phone='+996555000111',
        )
        self.profile = OrganizationProfile.objects.create(
            user=self.user,
            org_type=OrganizationProfile.OrgType.IE,
            tax_regime=OrganizationProfile.TaxRegime.SINGLE,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.QUARTERLY,
            onboarding_status=OrganizationProfile.OnboardingStatus.COMPLETED,
        )
        self.activity_trade = ActivityCode.objects.create(code='G47', section='G', name='Розничная торговля')
        self.activity_software = ActivityCode.objects.create(code='J62', section='J', name='Разработка программного обеспечения')
        self.activity_other = ActivityCode.objects.create(code='S95', section='S', name='Прочая услуга')
        OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.activity_trade,
            cash_tax_rate=Decimal('4.00'),
            non_cash_tax_rate=Decimal('2.00'),
            is_primary=True,
        )
        OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.activity_software,
            cash_tax_rate=Decimal('2.00'),
            non_cash_tax_rate=Decimal('1.00'),
            is_primary=False,
        )
        OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.activity_other,
            cash_tax_rate=Decimal('6.00'),
            non_cash_tax_rate=Decimal('4.00'),
            is_primary=False,
        )
        self.income_category = Category.objects.create(
            name='Доход',
            category_type=Category.CategoryType.INCOME,
            user=self.user,
        )

    def _income(self, amount, when, payment_method, activity, is_business=True, is_taxable=True):
        return Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            activity_code=activity,
            is_business=is_business,
            payment_method=payment_method,
            is_taxable=is_taxable,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=amount,
            description='Доход',
            transaction_date=when,
        )

    def test_builder_maps_transactions_to_official_cells_and_totals(self):
        self._income('1000.00', date(2026, 1, 10), Transaction.PaymentMethod.CASH, self.activity_trade)
        self._income('500.00', date(2026, 1, 15), Transaction.PaymentMethod.NON_CASH, self.activity_trade)
        self._income('300.00', date(2026, 2, 5), Transaction.PaymentMethod.NON_CASH, self.activity_software)
        self._income('200.00', date(2026, 3, 2), Transaction.PaymentMethod.CASH, self.activity_other)
        self._income('99.00', date(2026, 3, 5), Transaction.PaymentMethod.CASH, self.activity_other, is_business=False)
        self._income('77.00', date(2026, 3, 6), Transaction.PaymentMethod.CASH, self.activity_other, is_taxable=False)

        builder = STI091ReportDataBuilder(
            self.profile,
            2026,
            1,
            tin='12345678901234',
            taxpayer_name='ОсОО Тест',
            tax_office='УГНС по Октябрьскому району',
            contact_phone='+996555000111',
            activity_line_map={
                str(self.activity_trade.id): 'trade_general',
                self.activity_software.code: 'production',
                str(self.activity_other.id): 'other',
            },
            current_period_advance_payments=[{'amount': '150.00', 'rate': '2.00', 'description': 'Аванс Q1'}],
            previous_period_advance_offsets=[{'amount': '50.00', 'rate': '2.00', 'description': 'Аванс прошлого периода'}],
        )
        report = builder.build_report_data()

        self.assertEqual(report['cells']['053'], '1000.00')
        self.assertEqual(report['cells']['054'], '4.00')
        self.assertEqual(report['cells']['055'], '40.00')
        self.assertEqual(report['cells']['056'], '500.00')
        self.assertEqual(report['cells']['057'], '2.00')
        self.assertEqual(report['cells']['058'], '10.00')
        self.assertEqual(report['cells']['059'], '50.00')
        self.assertEqual(report['cells']['063'], '300.00')
        self.assertEqual(report['cells']['064'], '1.00')
        self.assertEqual(report['cells']['065'], '3.00')
        self.assertEqual(report['cells']['066'], '3.00')
        self.assertEqual(report['cells']['067'], '200.00')
        self.assertEqual(report['cells']['068'], '6.00')
        self.assertEqual(report['cells']['069'], '12.00')
        self.assertEqual(report['cells']['182'], '150.00')
        self.assertEqual(report['cells']['183'], '3.00')
        self.assertEqual(report['cells']['184'], '50.00')
        self.assertEqual(report['cells']['185'], '1.00')
        self.assertEqual(report['cells']['186'], '2100.00')
        self.assertEqual(report['cells']['187'], '67.00')
        self.assertTrue(report['ready_for_submission'])
        self.assertEqual(report['form_version'], '9')
        self.assertEqual(report['period']['start'], '2026-01-01')
        self.assertEqual(report['period']['end'], '2026-03-31')
        self.assertEqual(report['header']['105'], '+996555000111')
        self.assertEqual(report['advance_tables']['current_period_advance_payments'][0]['tax'], '3.00')

    def test_builder_flags_multiple_rates_in_same_cell(self):
        self._income('100.00', date(2026, 1, 10), Transaction.PaymentMethod.CASH, self.activity_other)
        tx = self._income('100.00', date(2026, 1, 11), Transaction.PaymentMethod.CASH, self.activity_other)
        Transaction.objects.filter(pk=tx.pk).update(cash_tax_rate=Decimal('7.00'))

        builder = STI091ReportDataBuilder(
            self.profile,
            2026,
            1,
            tin='12345678901234',
            taxpayer_name='ОсОО Тест',
            tax_office='УГНС',
            contact_phone='+996555000111',
            activity_line_map={str(self.activity_other.id): 'other'},
        )
        report = builder.build_report_data()

        self.assertEqual(report['cells']['067'], '200.00')
        self.assertEqual(report['cells']['068'], '')
        self.assertEqual(report['cells']['069'], '13.00')
        self.assertFalse(report['ready_for_submission'])
        self.assertTrue(any(issue['code'] == 'multiple_rates_for_cell' for issue in report['issues']))

    def test_builder_regression_quarter_totals(self):
        scenarios = [
            (1, Decimal('1930.00')),
            (2, Decimal('7440.00')),
            (3, Decimal('6300.00')),
            (4, Decimal('9490.00')),
        ]
        for quarter, expected_tax in scenarios:
            when = {1: date(2025, 1, 10), 2: date(2025, 4, 10), 3: date(2025, 7, 10), 4: date(2025, 10, 10)}[quarter]
            tx = self._income(
                str(expected_tax),
                when,
                Transaction.PaymentMethod.CASH,
                self.activity_trade,
            )
            Transaction.objects.filter(pk=tx.pk).update(cash_tax_rate=Decimal('100.00'))
            builder = STI091ReportDataBuilder(
                self.profile,
                2025,
                quarter,
                activity_line_map={str(self.activity_trade.id): 'trade_general'},
            )
            report = builder.build_report_data()
            self.assertEqual(Decimal(report['cells']['187']), expected_tax)

        tx = self._income('2400.00', date(2025, 11, 10), Transaction.PaymentMethod.CASH, self.activity_trade)
        Transaction.objects.filter(pk=tx.pk).update(cash_tax_rate=Decimal('100.00'))
        amended_builder = STI091ReportDataBuilder(
            self.profile,
            2025,
            4,
            report_kind='amended',
            activity_line_map={str(self.activity_trade.id): 'trade_general'},
        )
        amended_report = amended_builder.build_report_data()
        self.assertEqual(Decimal(amended_report['cells']['187']), Decimal('11890.00'))


@override_settings(MEDIA_ROOT='/tmp/salyk-tax-report-tests-media')
class STI091ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='api-sti091@example.com', password='StrongPass123')
        self.client.force_authenticate(self.user)
        self.profile = OrganizationProfile.objects.create(
            user=self.user,
            org_type=OrganizationProfile.OrgType.IE,
            tax_regime=OrganizationProfile.TaxRegime.SINGLE,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.QUARTERLY,
            onboarding_status=OrganizationProfile.OnboardingStatus.COMPLETED,
        )
        self.activity = ActivityCode.objects.create(code='G47', section='G', name='Розничная торговля')
        OrganizationActivity.objects.create(
            profile=self.profile,
            activity=self.activity,
            cash_tax_rate=Decimal('4.00'),
            non_cash_tax_rate=Decimal('2.00'),
            is_primary=True,
        )
        income_category = Category.objects.create(
            name='Доход',
            category_type=Category.CategoryType.INCOME,
            user=self.user,
        )
        Transaction.objects.create(
            user=self.user,
            category=income_category,
            activity_code=self.activity,
            is_business=True,
            payment_method=Transaction.PaymentMethod.CASH,
            is_taxable=True,
            transaction_type=Transaction.TransactionType.INCOME,
            amount='1000.00',
            description='Доход',
            transaction_date=date(2026, 1, 10),
        )

    def test_generate_endpoint_returns_cells_and_pdf(self):
        response = self.client.post(
            '/api/tax/generate-sti-091/',
            {
                'year': 2026,
                'quarter': 1,
                'tin': '12345678901234',
                'taxpayer_name': 'ИП Тест',
                'tax_office': 'УГНС',
                'contact_phone': '+996555111222',
                'activity_line_map': {str(self.activity.id): 'trade_general'},
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('STI-091', response.data['verbal_report'])
        self.assertIn('ячейка 187', response.data['verbal_report'])
        self.assertIn('12345678901234', response.data['verbal_report'])
        self.assertIsInstance(response.data['ai_validation'], str)
        self.assertIn(response.data['ai_validation_status'], ['ok', 'unavailable'])
        self.assertTrue(response.data['pdf_file'])
        self.assertIn('готов', response.data['validation_summary'].lower())
