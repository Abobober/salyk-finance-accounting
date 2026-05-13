from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from activities.models import ActivityCode
from organization.models import OrganizationActivity, OrganizationProfile


User = get_user_model()


class OrganizationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='StrongPass123')
        self.client.force_authenticate(self.user)
        self.activity = ActivityCode.objects.create(code='A01', section='A', name='Test activity')

    def _create_ready_to_finalize_profile(self, **overrides):
        defaults = {
            'user': self.user,
            'org_type': OrganizationProfile.OrgType.IE,
            'tax_regime': OrganizationProfile.TaxRegime.SINGLE,
            'tax_period_type': OrganizationProfile.TaxPeriodType.PRESET,
            'tax_period_preset': OrganizationProfile.TaxPeriodPreset.MONTHLY,
            'inn': '12345678901234',
            'taxpayer_name': 'ИП Тестов Тест',
            'tax_authority_code': '101',
            'tax_authority_name': 'УГНС по г. Бишкек',
            'contact_phone': '+996555000111',
            'tin': '12345678901234',
            'tax_office_code': '101',
            'tax_office_name': 'УГНС по г. Бишкек',
        }
        defaults.update(overrides)
        profile = OrganizationProfile.objects.create(**defaults)
        OrganizationActivity.objects.create(
            profile=profile,
            activity=self.activity,
            cash_tax_rate=Decimal('2.00'),
            non_cash_tax_rate=Decimal('4.00'),
            is_primary=True,
        )
        return profile

    def test_profile_endpoint_creates_missing_profile(self):
        response = self.client.get('/api/organization/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OrganizationProfile.objects.filter(user=self.user).exists())

    def test_activity_create_works_without_precreated_profile(self):
        response = self.client.post('/api/organization/activities/', {
            'activity': self.activity.id,
            'cash_tax_rate': '2.00',
            'non_cash_tax_rate': '4.00',
            'is_primary': True,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.activities.count(), 1)

    def test_profile_patch_saves_required_organization_details(self):
        response = self.client.patch('/api/organization/profile/', {
            'tin': ' 12345678901234 ',
            'taxpayer_name': ' ИП Тестов Тест ',
            'tax_office_code': ' 101 ',
            'tax_office_name': ' УГНС по г. Бишкек ',
            'contact_phone': ' +996555000111 ',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.tin, '12345678901234')
        self.assertEqual(profile.taxpayer_name, 'ИП Тестов Тест')
        self.assertEqual(profile.tax_office_code, '101')
        self.assertEqual(profile.tax_office_name, 'УГНС по г. Бишкек')
        self.assertEqual(profile.contact_phone, '+996555000111')

    def test_profile_patch_rejects_whitespace_only_required_organization_details(self):
        response = self.client.patch('/api/organization/profile/', {
            'tin': '   ',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['tin'][0], 'This field may not be blank.')

    def test_switch_from_preset_to_custom_clears_preset_without_explicit_null(self):
        OrganizationProfile.objects.create(
            user=self.user,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.MONTHLY,
        )

        response = self.client.patch('/api/organization/profile/', {
            'tax_period_type': OrganizationProfile.TaxPeriodType.CUSTOM,
            'tax_period_custom_day': 15,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.tax_period_type, OrganizationProfile.TaxPeriodType.CUSTOM)
        self.assertIsNone(profile.tax_period_preset)
        self.assertEqual(profile.tax_period_custom_day, 15)

    def test_switch_from_custom_to_preset_keeps_start_day(self):
        OrganizationProfile.objects.create(
            user=self.user,
            tax_period_type=OrganizationProfile.TaxPeriodType.CUSTOM,
            tax_period_custom_day=20,
        )

        response = self.client.patch('/api/organization/profile/', {
            'tax_period_type': OrganizationProfile.TaxPeriodType.PRESET,
            'tax_period_preset': OrganizationProfile.TaxPeriodPreset.MONTHLY,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.tax_period_type, OrganizationProfile.TaxPeriodType.PRESET)
        self.assertEqual(profile.tax_period_preset, OrganizationProfile.TaxPeriodPreset.MONTHLY)
        self.assertEqual(profile.tax_period_custom_day, 20)

    def test_preset_period_allows_updating_start_day_without_switching_type(self):
        OrganizationProfile.objects.create(
            user=self.user,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.MONTHLY,
            tax_period_custom_day=5,
        )

        response = self.client.patch('/api/organization/profile/', {
            'tax_period_custom_day': 20,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.tax_period_type, OrganizationProfile.TaxPeriodType.PRESET)
        self.assertEqual(profile.tax_period_preset, OrganizationProfile.TaxPeriodPreset.MONTHLY)
        self.assertEqual(profile.tax_period_custom_day, 20)

    def test_tax_period_endpoint_uses_preset_start_day(self):
        OrganizationProfile.objects.create(
            user=self.user,
            tax_period_type=OrganizationProfile.TaxPeriodType.PRESET,
            tax_period_preset=OrganizationProfile.TaxPeriodPreset.MONTHLY,
            tax_period_custom_day=20,
        )

        fixed_now = datetime(2026, 3, 25, 10, 0, tzinfo=timezone.get_current_timezone())
        with patch('organization.tax_period_utils.timezone.now', return_value=fixed_now):
            response = self.client.get('/api/organization/tax-period/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['current_period']['start'], '2026-03-20')
        self.assertEqual(response.data['current_period']['end'], '2026-04-19')
        self.assertEqual(response.data['next_period_start'], '2026-04-20')

    def test_only_one_primary_activity_allowed_per_profile(self):
        profile = OrganizationProfile.objects.create(user=self.user)
        OrganizationActivity.objects.create(
            profile=profile,
            activity=self.activity,
            cash_tax_rate=Decimal('2.00'),
            non_cash_tax_rate=Decimal('4.00'),
            is_primary=True,
        )

        second_activity = ActivityCode.objects.create(code='A02', section='A', name='Second activity')

        with self.assertRaises(IntegrityError):
            OrganizationActivity.objects.create(
                profile=profile,
                activity=second_activity,
                cash_tax_rate=Decimal('1.00'),
                non_cash_tax_rate=Decimal('3.00'),
                is_primary=True,
            )

    def test_finalize_requires_inn(self):
        self._create_ready_to_finalize_profile(inn=None, tin=None)

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'INN is required.')

    def test_finalize_requires_tax_period(self):
        self._create_ready_to_finalize_profile(
            tax_period_type=None,
            tax_period_preset=None,
        )

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'Tax period is required.')

    def test_finalize_requires_taxpayer_name(self):
        self._create_ready_to_finalize_profile(taxpayer_name='   ')

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'Taxpayer name is required.')

    def test_finalize_requires_tax_authority_details(self):
        self._create_ready_to_finalize_profile(tax_authority_code=None)

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'Tax authority code is required.')

        OrganizationProfile.objects.filter(user=self.user).delete()
        self._create_ready_to_finalize_profile(tax_authority_name='   ')

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'Tax authority name is required.')

    def test_finalize_requires_contact_phone(self):
        self._create_ready_to_finalize_profile(contact_phone='')

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['non_field_errors'][0], 'Contact phone is required.')

    def test_finalize_succeeds_with_full_organization_details(self):
        self._create_ready_to_finalize_profile()

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.onboarding_status, OrganizationProfile.OnboardingStatus.COMPLETED)
        self.assertEqual(profile.tin, profile.inn)

    def test_finalize_copies_inn_to_tin_when_tin_empty(self):
        self._create_ready_to_finalize_profile(tin=None, inn='99887766554433')

        response = self.client.patch('/api/organization/finalize/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        profile = OrganizationProfile.objects.get(user=self.user)
        self.assertEqual(profile.tin, '99887766554433')
