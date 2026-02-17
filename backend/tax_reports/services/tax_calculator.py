from decimal import Decimal
from .tax_config import UNIFIED_TAX_RATES, SOCIAL_FUND


class UnifiedTaxCalculator:

    def __init__(self, organization, transactions, year, quarter):
        self.organization = organization
        self.transactions = transactions
        self.year = year
        self.quarter = quarter

    def get_turnover(self):
        return sum(
            Decimal(str(t.amount))
            for t in self.transactions
            if t.type == "income"
        )

    def get_region_key(self):
        region = self.organization.region.lower()
        if region in ["bishkek", "chui"]:
            return region
        return "other"

    def get_rate(self):
        regime = self.organization.tax_regime
        region = self.get_region_key()
        return UNIFIED_TAX_RATES[regime][region]

    def calculate_social_fund(self, turnover):
        monthly_income = turnover / Decimal("3")
        threshold = SOCIAL_FUND["threshold"]

        extra = Decimal("0")
        if monthly_income > threshold:
            extra = (monthly_income - threshold) * SOCIAL_FUND["extra_percent"] * 3

        fixed = SOCIAL_FUND["fixed_monthly"] * 3
        return fixed + extra

    def build(self):
        turnover = self.get_turnover()
        rate = self.get_rate()
        unified_tax = turnover * rate
        social = self.calculate_social_fund(turnover)

        return {
            "year": self.year,
            "quarter": self.quarter,
            "organization_name": self.organization.name,
            "inn": self.organization.inn,
            "turnover": turnover,
            "rate": rate,
            "unified_tax": unified_tax,
            "social_fund": social,
            "total_payable": unified_tax + social
        }
