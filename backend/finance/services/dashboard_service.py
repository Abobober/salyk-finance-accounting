"""Dashboard service: aggregates via annotate and cache."""

from django.conf import settings
from django.db.models import Q, Sum

from finance.cache_utils import build_finance_cache_key, get_cached_finance_payload
from finance.constants import DEFAULT_RECENT_TRANSACTIONS_LIMIT, ZERO
from finance.models import Transaction
from finance.querysets import apply_transaction_query_filters


def _build_dashboard_data(user, recent_limit=DEFAULT_RECENT_TRANSACTIONS_LIMIT, filters=None):
    base_qs = Transaction.objects.filter(user=user)
    base_qs = apply_transaction_query_filters(base_qs, filters)

    totals = base_qs.aggregate(
        total_income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
        total_expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
    )
    total_income = totals['total_income'] or ZERO
    total_expense = totals['total_expense'] or ZERO

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


def get_dashboard_data(user, recent_limit=DEFAULT_RECENT_TRANSACTIONS_LIMIT, filters=None):
    cache_key = build_finance_cache_key(
        'dashboard',
        user.id,
        payload={
            'recent_limit': recent_limit,
            'filters': filters,
        },
    )
    return get_cached_finance_payload(
        cache_key,
        builder=lambda: _build_dashboard_data(user, recent_limit=recent_limit, filters=filters),
        ttl=settings.DASHBOARD_CACHE_TTL,
    )
