"""Dashboard service: aggregates via annotate."""

from django.db.models import Q, Sum

from finance.constants import DEFAULT_RECENT_TRANSACTIONS_LIMIT, ZERO
from finance.models import Transaction


def get_dashboard_data(user, recent_limit=DEFAULT_RECENT_TRANSACTIONS_LIMIT):
    """
    Build dashboard payload: totals (annotate), by_category (annotate), recent_transactions.
    Uses annotate/aggregate only; no N+1.
    """
    base_qs = Transaction.objects.filter(user=user)

    # Totals via aggregate with conditional Sum
    totals = base_qs.aggregate(
        total_income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
        total_expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
    )
    total_income = totals['total_income'] or ZERO
    total_expense = totals['total_expense'] or ZERO

    # By category via values + annotate
    by_category = (
        base_qs.values('category__name', 'category__category_type')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    by_category_list = [
        {
            'category_name': row['category__name'],
            'category_type': row['category__category_type'],
            'total': str(row['total']),
        }
        for row in by_category
    ]

    # Recent transactions (last N)
    recent = (
        base_qs.select_related('category', 'activity_code')
        .order_by('-transaction_date', '-created_at')[:recent_limit]
    )
    recent_list = [
        {
            'id': t.id,
            'amount': str(t.amount),
            'transaction_type': t.transaction_type,
            'category_name': t.category.name if t.category else None,
            'description': t.description,
            'transaction_date': t.transaction_date.isoformat(),
            'created_at': t.created_at.isoformat(),
            'payment_method': t.payment_method,
        }
        for t in recent
    ]

    return {
        'totals': {
            'total_income': str(total_income),
            'total_expense': str(total_expense),
        },
        'by_category': by_category_list,
        'recent_transactions': recent_list,
    }

