"""Utilities for calculating tax periods based on organization settings."""

from datetime import date, timedelta
from typing import Optional, Tuple

from .models import OrganizationProfile


def get_current_tax_period_start_end(profile: OrganizationProfile, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """
    Calculate current tax period start and end dates based on organization's tax period settings.
    
    Args:
        profile: OrganizationProfile instance with tax_period settings
        reference_date: Date to calculate from (defaults to today)
    
    Returns:
        Tuple of (period_start, period_end) dates
    
    Raises:
        ValueError: If tax_period_type is not set or invalid
    """
    if reference_date is None:
        from django.utils import timezone
        reference_date = timezone.now().date()
    
    if not profile.tax_period_type:
        raise ValueError("Tax period type is not set for this organization.")
    
    if profile.tax_period_type == OrganizationProfile.TaxPeriodType.PRESET:
        return _get_preset_period_dates(profile.tax_period_preset, reference_date)
    elif profile.tax_period_type == OrganizationProfile.TaxPeriodType.CUSTOM:
        return _get_custom_period_dates(profile.tax_period_custom_day, reference_date)
    else:
        raise ValueError(f"Invalid tax_period_type: {profile.tax_period_type}")


def _get_preset_period_dates(preset: str, reference_date: date) -> Tuple[date, date]:
    """Calculate dates for preset tax periods."""
    if preset == OrganizationProfile.TaxPeriodPreset.MONTHLY:
        # Current month: 1st to last day of month
        period_start = reference_date.replace(day=1)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1) - timedelta(days=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1) - timedelta(days=1)
        return period_start, period_end
    
    elif preset == OrganizationProfile.TaxPeriodPreset.QUARTERLY:
        # Current quarter: 1st of quarter start month to last day of quarter end month
        quarter = (reference_date.month - 1) // 3
        quarter_start_month = quarter * 3 + 1
        period_start = reference_date.replace(month=quarter_start_month, day=1)
        
        quarter_end_month = quarter_start_month + 2
        if quarter_end_month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1) - timedelta(days=1)
        else:
            period_end = period_start.replace(month=quarter_end_month + 1) - timedelta(days=1)
        return period_start, period_end
    
    elif preset == OrganizationProfile.TaxPeriodPreset.YEARLY:
        # Current year: Jan 1 to Dec 31
        period_start = reference_date.replace(month=1, day=1)
        period_end = reference_date.replace(month=12, day=31)
        return period_start, period_end
    
    else:
        raise ValueError(f"Invalid tax_period_preset: {preset}")


def _get_custom_period_dates(custom_day: int, reference_date: date) -> Tuple[date, date]:
    """
    Calculate dates for custom tax period (e.g., 20th of each month).
    
    Example: If custom_day=20 and today is Feb 15, period is Jan 20 - Feb 19.
             If custom_day=20 and today is Feb 25, period is Feb 20 - Mar 19.
    
    Handles edge cases: if custom_day=31 and month has fewer days, uses last day of month.
    """
    if custom_day < 1 or custom_day > 31:
        raise ValueError(f"Invalid custom_day: {custom_day}. Must be 1-31.")
    
    def _safe_date(year: int, month: int, day: int) -> date:
        """Create date, handling months with fewer days (e.g., day 31 in Feb -> Feb 28/29)."""
        from calendar import monthrange
        max_day = monthrange(year, month)[1]
        actual_day = min(day, max_day)
        return date(year, month, actual_day)
    
    # Determine which period we're in based on custom_day
    if reference_date.day < custom_day:
        # Current period started last month on custom_day
        if reference_date.month == 1:
            # Last month was December of previous year
            period_start = _safe_date(reference_date.year - 1, 12, custom_day)
            # Period ends the day before custom_day of current month
            period_end = _safe_date(reference_date.year, reference_date.month, custom_day) - timedelta(days=1)
        else:
            period_start = _safe_date(reference_date.year, reference_date.month - 1, custom_day)
            period_end = _safe_date(reference_date.year, reference_date.month, custom_day) - timedelta(days=1)
    else:
        # Current period started this month on custom_day
        period_start = _safe_date(reference_date.year, reference_date.month, custom_day)
        # Period ends the day before custom_day of next month
        if reference_date.month == 12:
            period_end = _safe_date(reference_date.year + 1, 1, custom_day) - timedelta(days=1)
        else:
            period_end = _safe_date(reference_date.year, reference_date.month + 1, custom_day) - timedelta(days=1)
    
    return period_start, period_end


def get_next_tax_period_start(profile: OrganizationProfile, reference_date: Optional[date] = None) -> date:
    """Get the start date of the next tax period."""
    _, current_end = get_current_tax_period_start_end(profile, reference_date)
    return current_end + timedelta(days=1)
