from datetime import date
from decimal import Decimal

from finance.models import Transaction


class ReportDataBuilder:
    def __init__(self, organization, year, quarter):
        self.organization = organization
        self.year = year
        self.quarter = quarter

    def get_period_dates(self):
        if self.quarter == 1:
            return date(self.year, 1, 1), date(self.year, 3, 31)
        if self.quarter == 2:
            return date(self.year, 4, 1), date(self.year, 6, 30)
        if self.quarter == 3:
            return date(self.year, 7, 1), date(self.year, 9, 30)
        return date(self.year, 10, 1), date(self.year, 12, 31)

    def get_transactions(self):
        start, end = self.get_period_dates()
        return Transaction.objects.filter(
            user=self.organization.user,
            transaction_type=Transaction.TransactionType.INCOME,
            is_business=True,
            is_taxable=True,
            transaction_date__range=(start, end),
        )

    def build_report_data(self):
        transactions = self.get_transactions()
        turnover = sum((t.amount for t in transactions), Decimal("0.00"))

        rate = Decimal("10.00")
        unified_tax = turnover * rate / Decimal("100.00")
        social_fund = turnover * Decimal("3.00") / Decimal("100.00")
        total_payable = unified_tax + social_fund

        report_data = {
            "year": self.year,
            "quarter": self.quarter,
            "organization_name": self.organization.user.email,
            "inn": getattr(self.organization, "inn", "000000000"),
            "turnover": turnover,
            "rate": rate,
            "unified_tax": unified_tax,
            "social_fund": social_fund,
            "total_payable": total_payable,
        }
        return report_data
