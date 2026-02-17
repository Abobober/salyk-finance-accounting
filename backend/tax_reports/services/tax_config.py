from decimal import Decimal

UNIFIED_TAX_RATES = {
    "trade": {
        "bishkek": Decimal("0.02"),
        "chui": Decimal("0.02"),
        "other": Decimal("0.01"),
    },
    "production": {
        "bishkek": Decimal("0.01"),
        "chui": Decimal("0.01"),
        "other": Decimal("0.005"),
    }
}

SOCIAL_FUND = {
    "fixed_monthly": Decimal("1200"),
    "extra_percent": Decimal("0.03"),
    "threshold": Decimal("20000"),
}

VAT_THRESHOLD = Decimal("8000000")
