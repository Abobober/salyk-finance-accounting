"""Utility functions for finance app."""

from datetime import timedelta

from django.utils import timezone

from finance.constants import (
    DATE_FORMAT,
    PRESET_MONTH_DAYS,
    PRESET_WEEK_DAYS,
    PRESET_YEAR_DAYS,
)


def parse_date_param(date_str, param_name='date'):
    """
    Parse date string from query params.
    
    Returns:
        tuple: (date_object, error_response)
        - If date_str is None/empty: (None, None)
        - If valid: (date_object, None)
        - If invalid: (None, error_dict)
    """
    if not date_str:
        return None, None
    
    try:
        from datetime import datetime
        return datetime.strptime(date_str, DATE_FORMAT).date(), None
    except ValueError:
        return None, {'error': f'Invalid {param_name} format. Use YYYY-MM-DD'}


def get_preset_dates(preset):
    """
    Get date_from and date_to for preset periods.
    
    Args:
        preset: 'week', 'month', 'year', 'all_time'
    
    Returns:
        tuple: (date_from, date_to) or (None, None) for 'all_time'
    """
    if preset == 'all_time':
        return None, None
    
    date_to = timezone.now().date()
    
    if preset == 'week':
        date_from = date_to - timedelta(days=PRESET_WEEK_DAYS)
    elif preset == 'month':
        date_from = date_to - timedelta(days=PRESET_MONTH_DAYS)
    elif preset == 'year':
        date_from = date_to - timedelta(days=PRESET_YEAR_DAYS)
    else:
        return None, None
    
    return date_from, date_to


def update_instance_from_dict(instance, data):
    """Update model instance attributes from dictionary."""
    for attr, value in data.items():
        setattr(instance, attr, value)
    instance.save()
    return instance
