from django.contrib.auth import get_user_model
from django.test import TestCase

from activities.models import ActivityCode
from finance.models import Transaction
from organization.models import OrganizationActivity
from organization.models import OrganizationProfile

from .services.report_data_builder import STI091ReportDataBuilder


class STI091ReportDataBuilderProfileDefaultsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='owner@example.com',
            password='password',
            phone='+996700111222',
        )
        self.organization = OrganizationProfile.objects.create(
            user=self.user,
            org_type=OrganizationProfile.OrgType.IE,
            tax_regime=OrganizationProfile.TaxRegime.SINGLE,
            inn='12345678901234',
            taxpayer_name='ОсОО Тест',
            tax_authority_code='001',
            tax_authority_name='УГНС Ленинского района',
            contact_phone='+996555123456',
        )
        self.activity = ActivityCode.objects.create(
            code='56.1',
            section='G',
            name='Деятельность ресторанов и предоставление мобильных услуг по обеспечению пищей',
        )
        OrganizationActivity.objects.create(
            profile=self.organization,
            activity=self.activity,
            cash_tax_rate='3.00',
            non_cash_tax_rate='6.00',
            is_primary=True,
        )

    def test_uses_organization_registration_data_when_request_fields_are_empty(self):
        report_data = STI091ReportDataBuilder(self.organization, 2026, 1).build_report_data()

        self.assertEqual(report_data['header']['102'], '12345678901234')
        self.assertEqual(report_data['header']['103'], 'ОсОО Тест')
        self.assertEqual(report_data['header']['104'], '001 УГНС Ленинского района')
        self.assertEqual(report_data['header']['104_code'], '001')
        self.assertEqual(report_data['header']['104_name'], 'УГНС Ленинского района')
        self.assertEqual(report_data['header']['105'], '+996555123456')
        self.assertFalse(any(issue['code'] == 'missing_tin' for issue in report_data['issues']))
        self.assertFalse(any(issue['code'] == 'missing_taxpayer_name' for issue in report_data['issues']))

    def test_ie_uses_user_full_name_when_taxpayer_name_is_empty(self):
        self.user.first_name = 'Айбек'
        self.user.last_name = 'Ибраев'
        self.user.save(update_fields=['first_name', 'last_name'])
        self.organization.taxpayer_name = ''
        self.organization.save(update_fields=['taxpayer_name'])

        report_data = STI091ReportDataBuilder(self.organization, 2026, 1).build_report_data()

        self.assertEqual(report_data['header']['103'], 'Айбек Ибраев')

    def test_request_fields_still_override_organization_defaults(self):
        report_data = STI091ReportDataBuilder(
            self.organization,
            2026,
            1,
            tin='99999999999999',
            taxpayer_name='Ручное имя',
            tax_office='777 Ручная налоговая',
            contact_phone='+996500000000',
        ).build_report_data()

        self.assertEqual(report_data['header']['102'], '99999999999999')
        self.assertEqual(report_data['header']['103'], 'Ручное имя')
        self.assertEqual(report_data['header']['104'], '777 Ручная налоговая')
        self.assertEqual(report_data['header']['105'], '+996500000000')

    def test_empty_rows_keep_fixed_form_rates(self):
        report_data = STI091ReportDataBuilder(self.organization, 2026, 2).build_report_data()

        self.assertEqual(report_data['cells']['051'], '0.50')
        self.assertEqual(report_data['cells']['054'], '4.00')
        self.assertEqual(report_data['cells']['057'], '2.00')
        self.assertEqual(report_data['cells']['068'], '6.00')
        self.assertEqual(report_data['cells']['071'], '4.00')
        self.assertEqual(report_data['cells']['140'], '8.00')

    def test_primary_public_catering_rates_are_used_for_missing_activity_transactions(self):
        Transaction.objects.create(
            user=self.user,
            transaction_type=Transaction.TransactionType.INCOME,
            amount='1000.00',
            transaction_date='2026-04-15',
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=False,
            is_taxable=True,
        )

        report_data = STI091ReportDataBuilder(self.organization, 2026, 2).build_report_data()

        self.assertEqual(report_data['cells']['074'], '1000.00')
        self.assertEqual(report_data['cells']['075'], '3.00')
        self.assertEqual(report_data['cells']['076'], '30.00')
        self.assertEqual(report_data['cells']['186'], '1000.00')
        self.assertEqual(report_data['cells']['187'], '30.00')

    def test_activity_code_56_uses_public_catering_rows_and_registered_rates(self):
        Transaction.objects.create(
            user=self.user,
            activity_code=self.activity,
            transaction_type=Transaction.TransactionType.INCOME,
            amount='1000.00',
            transaction_date='2026-04-15',
            payment_method=Transaction.PaymentMethod.CASH,
            is_business=True,
            is_taxable=True,
        )
        Transaction.objects.create(
            user=self.user,
            activity_code=self.activity,
            transaction_type=Transaction.TransactionType.INCOME,
            amount='500.00',
            transaction_date='2026-04-16',
            payment_method=Transaction.PaymentMethod.NON_CASH,
            is_business=True,
            is_taxable=True,
        )

        report_data = STI091ReportDataBuilder(self.organization, 2026, 2).build_report_data()

        self.assertEqual(report_data['cells']['074'], '1000.00')
        self.assertEqual(report_data['cells']['075'], '3.00')
        self.assertEqual(report_data['cells']['076'], '30.00')
        self.assertEqual(report_data['cells']['077'], '500.00')
        self.assertEqual(report_data['cells']['078'], '6.00')
        self.assertEqual(report_data['cells']['079'], '30.00')
