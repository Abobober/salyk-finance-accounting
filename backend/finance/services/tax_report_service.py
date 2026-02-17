"""
Tax report for a chosen period. Uses transactions + org tax settings.
No separate app: tax period settings live in organization, report data in finance.
"""

from decimal import Decimal

from django.db.models import Q, Sum

from finance.constants import ZERO
from finance.models import Transaction


def build_tax_report(user, date_from, date_to):
    """
    Build tax report data for the given period.
    
    Returns aggregates: totals by type, by payment method (with tax amounts),
    taxable vs non-taxable, and by activity code for business transactions.
    """
    qs = Transaction.objects.filter(
        user=user,
        transaction_date__gte=date_from,
        transaction_date__lte=date_to
    )

    # Overall totals
    totals = qs.aggregate(
        total_income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
        total_expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
    )
    total_income = totals['total_income'] or ZERO
    total_expense = totals['total_expense'] or ZERO

    # Taxable vs non-taxable
    taxable = qs.filter(is_taxable=True).aggregate(
        income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
        expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
    )
    non_taxable = qs.filter(is_taxable=False).aggregate(
        income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
        expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
    )

    # By payment method (cash / non_cash)
    by_payment = []
    for method, label in Transaction.PaymentMethod.choices:
        method_qs = qs.filter(payment_method=method)
        agg = method_qs.aggregate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
        )
        income = agg['income'] or ZERO
        expense = agg['expense'] or ZERO
        by_payment.append({
            'payment_method': method,
            'payment_method_display': label,
            'income': str(income),
            'expense': str(expense),
            'net': str(income - expense),
        })

    # By activity code (business transactions)
    by_activity = list(
        qs.filter(is_business=True, activity_code__isnull=False)
        .values('activity_code', 'activity_code__name')
        .annotate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
        )
        .order_by('-income')
    )
    by_activity_list = [
        {
            'activity_code_id': r['activity_code'],
            'activity_name': r['activity_code__name'],
            'income': str(r['income'] or ZERO),
            'expense': str(r['expense'] or ZERO),
            'net': str((r['income'] or ZERO) - (r['expense'] or ZERO)),
        }
        for r in by_activity
    ]

    return {
        'period': {
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
        },
        'totals': {
            'total_income': str(total_income),
            'total_expense': str(total_expense),
            'net': str(total_income - total_expense),
        },
        'taxable': {
            'income': str(taxable['income'] or ZERO),
            'expense': str(taxable['expense'] or ZERO),
        },
        'non_taxable': {
            'income': str(non_taxable['income'] or ZERO),
            'expense': str(non_taxable['expense'] or ZERO),
        },
        'by_payment_method': by_payment,
        'by_activity': by_activity_list,
    }
