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
