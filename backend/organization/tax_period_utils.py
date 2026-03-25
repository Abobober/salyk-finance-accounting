"""Utilities for calculating tax periods based on organization settings."""

from calendar import monthrange
from datetime import date, timedelta
from typing import Optional, Tuple

from django.utils import timezone

from .models import OrganizationProfile


def get_current_tax_period_start_end(profile: OrganizationProfile, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """Calculate current tax period start and end dates."""
    if reference_date is None:
        reference_date = timezone.now().date()

    if not profile.tax_period_type:
        raise ValueError('Tax period type is not set for this organization.')

    if profile.tax_period_type == OrganizationProfile.TaxPeriodType.PRESET:
        return _get_preset_period_dates(
            profile.tax_period_preset,
            reference_date,
            profile.tax_period_custom_day,
        )
    if profile.tax_period_type == OrganizationProfile.TaxPeriodType.CUSTOM:
        return _get_custom_period_dates(profile.tax_period_custom_day, reference_date)
    raise ValueError(f'Invalid tax_period_type: {profile.tax_period_type}')


def _safe_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def _shift_year_month(year: int, month: int, delta_months: int) -> Tuple[int, int]:
    shifted = year * 12 + (month - 1) + delta_months
    return shifted // 12, shifted % 12 + 1


def _get_recurring_period_dates(
    reference_date: date,
    cycle_year: int,
    cycle_month: int,
    month_span: int,
    anchor_day: int,
) -> Tuple[date, date]:
    period_start = _safe_date(cycle_year, cycle_month, anchor_day)

    if reference_date < period_start:
        cycle_year, cycle_month = _shift_year_month(cycle_year, cycle_month, -month_span)
        period_start = _safe_date(cycle_year, cycle_month, anchor_day)

    next_year, next_month = _shift_year_month(cycle_year, cycle_month, month_span)
    period_end = _safe_date(next_year, next_month, anchor_day) - timedelta(days=1)
    return period_start, period_end


def _get_preset_period_dates(preset: str, reference_date: date, custom_day: Optional[int] = None) -> Tuple[date, date]:
    """Calculate dates for preset tax periods with an optional custom start day."""
    anchor_day = custom_day or 1

    if preset == OrganizationProfile.TaxPeriodPreset.MONTHLY:
        return _get_recurring_period_dates(
            reference_date,
            reference_date.year,
            reference_date.month,
            1,
            anchor_day,
        )

    if preset == OrganizationProfile.TaxPeriodPreset.QUARTERLY:
        quarter = (reference_date.month - 1) // 3
        quarter_start_month = quarter * 3 + 1
        return _get_recurring_period_dates(
            reference_date,
            reference_date.year,
            quarter_start_month,
            3,
            anchor_day,
        )

    if preset == OrganizationProfile.TaxPeriodPreset.YEARLY:
        return _get_recurring_period_dates(
            reference_date,
            reference_date.year,
            1,
            12,
            anchor_day,
        )

    raise ValueError(f'Invalid tax_period_preset: {preset}')


def _get_custom_period_dates(custom_day: int, reference_date: date) -> Tuple[date, date]:
    """Calculate dates for a custom monthly tax period."""
    if custom_day < 1 or custom_day > 31:
        raise ValueError(f'Invalid custom_day: {custom_day}. Must be 1-31.')

    return _get_recurring_period_dates(
        reference_date,
        reference_date.year,
        reference_date.month,
        1,
        custom_day,
    )


def get_next_tax_period_start(profile: OrganizationProfile, reference_date: Optional[date] = None) -> date:
    """Get the start date of the next tax period."""
    _, current_end = get_current_tax_period_start_end(profile, reference_date)
    return current_end + timedelta(days=1)
