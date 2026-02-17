"""
Constants for finance app - avoid hardcoding values.
"""

from decimal import Decimal

# Monetary limits
MAX_TRANSACTION_AMOUNT = Decimal("1000000000")
MIN_TRANSACTION_AMOUNT = Decimal("0.01")
ZERO = Decimal("0")

# Default limits
DEFAULT_RECENT_TRANSACTIONS_LIMIT = 10
DEFAULT_CATEGORY_BREAKDOWN_LIMIT = 10
DEFAULT_ANALYTICS_DAYS = 365

# Preset periods (days)
PRESET_WEEK_DAYS = 7
PRESET_MONTH_DAYS = 30
PRESET_YEAR_DAYS = 365

# Date formats
DATE_FORMAT = '%Y-%m-%d'
MONTH_FORMAT = '%Y-%m'
YEAR_FORMAT = '%Y'
