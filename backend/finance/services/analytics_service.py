"""Analytics service for graphs with cache support."""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from finance.cache_utils import build_finance_cache_key, get_cached_finance_payload
from finance.constants import (
    DATE_FORMAT,
    DEFAULT_ANALYTICS_DAYS,
    DEFAULT_CATEGORY_BREAKDOWN_LIMIT,
    MONTH_FORMAT,
    YEAR_FORMAT,
    ZERO,
)
from finance.models import Transaction
from finance.querysets import apply_transaction_query_filters


def _build_time_series_data(user, period='monthly', date_from=None, date_to=None, transaction_type=None, filters=None):
    base_qs = Transaction.objects.filter(user=user)
    base_qs = apply_transaction_query_filters(base_qs, filters)

    if date_from:
        base_qs = base_qs.filter(transaction_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(transaction_date__lte=date_to)
    if transaction_type:
        base_qs = base_qs.filter(transaction_type=transaction_type)

    if not date_from and not date_to:
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=DEFAULT_ANALYTICS_DAYS)
        base_qs = base_qs.filter(transaction_date__gte=date_from, transaction_date__lte=date_to)

    period_configs = {
        'daily': ('transaction_date', DATE_FORMAT),
        'monthly': ('month', MONTH_FORMAT),
        'yearly': ('year', YEAR_FORMAT),
    }
    date_trunc, date_format = period_configs.get(period, ('month', MONTH_FORMAT))

    if date_trunc == 'transaction_date':
        qs = base_qs.values('transaction_date').annotate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
        ).order_by('transaction_date')

        result = []
        for row in qs:
            income = row['income'] or ZERO
            expense = row['expense'] or ZERO
            result.append({
                'period': row['transaction_date'].strftime(date_format),
                'income': str(income),
                'expense': str(expense),
                'net': str(income - expense),
            })
        return result

    if date_trunc == 'month':
        qs = base_qs.annotate(period=TruncMonth('transaction_date')).values('period').annotate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
        ).order_by('period')
    else:
        qs = base_qs.annotate(period=TruncYear('transaction_date')).values('period').annotate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
        ).order_by('period')

    result = []
    for row in qs:
        period_str = row['period'].strftime(date_format) if row['period'] else ''
        income = row['income'] or ZERO
        expense = row['expense'] or ZERO
        result.append({
            'period': period_str,
            'income': str(income),
            'expense': str(expense),
            'net': str(income - expense),
        })

    return result


def get_time_series_data(user, period='monthly', date_from=None, date_to=None, transaction_type=None, filters=None):
    cache_key = build_finance_cache_key(
        'analytics:time_series',
        user.id,
        payload={
            'period': period,
            'date_from': date_from,
            'date_to': date_to,
            'transaction_type': transaction_type,
            'filters': filters,
        },
    )
    return get_cached_finance_payload(
        cache_key,
        builder=lambda: _build_time_series_data(
            user,
            period=period,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type,
            filters=filters,
        ),
        ttl=settings.FINANCE_CACHE_TTL,
    )


def _build_category_breakdown(user, date_from=None, date_to=None, transaction_type=None, limit=DEFAULT_CATEGORY_BREAKDOWN_LIMIT, filters=None):
    base_qs = Transaction.objects.filter(user=user)
    base_qs = apply_transaction_query_filters(base_qs, filters)

    if date_from:
        base_qs = base_qs.filter(transaction_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(transaction_date__lte=date_to)
    if transaction_type:
        base_qs = base_qs.filter(transaction_type=transaction_type)

    qs = (
        base_qs.values('category__name', 'category__category_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .filter(category__name__isnull=False)
        .order_by('-total')[:limit]
    )

    return [
        {
            'category_name': row['category__name'],
            'category_type': row['category__category_type'],
            'total': str(row['total'] or ZERO),
            'count': row['count'],
        }
        for row in qs
    ]


def get_category_breakdown(user, date_from=None, date_to=None, transaction_type=None, limit=DEFAULT_CATEGORY_BREAKDOWN_LIMIT, filters=None):
    cache_key = build_finance_cache_key(
        'analytics:category_breakdown',
        user.id,
        payload={
            'date_from': date_from,
            'date_to': date_to,
            'transaction_type': transaction_type,
            'limit': limit,
            'filters': filters,
        },
    )
    return get_cached_finance_payload(
        cache_key,
        builder=lambda: _build_category_breakdown(
            user,
            date_from=date_from,
            date_to=date_to,
            transaction_type=transaction_type,
            limit=limit,
            filters=filters,
        ),
        ttl=settings.FINANCE_CACHE_TTL,
    )


def _build_period_comparison(user, period1_from, period1_to, period2_from, period2_to):
    def get_period_stats(date_from, date_to):
        qs = Transaction.objects.filter(
            user=user,
            transaction_date__gte=date_from,
            transaction_date__lte=date_to,
        )

        stats = qs.aggregate(
            income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
            expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
            count=Count('id'),
        )

        income = stats['income'] or ZERO
        expense = stats['expense'] or ZERO
        net = income - expense

        return {
            'income': str(income),
            'expense': str(expense),
            'net': str(net),
            'transaction_count': stats['count'],
        }

    p1 = get_period_stats(period1_from, period1_to)
    p2 = get_period_stats(period2_from, period2_to)

    p1_income = Decimal(p1['income'])
    p1_expense = Decimal(p1['expense'])
    p1_net = Decimal(p1['net'])

    p2_income = Decimal(p2['income'])
    p2_expense = Decimal(p2['expense'])
    p2_net = Decimal(p2['net'])

    income_change = p2_income - p1_income
    expense_change = p2_expense - p1_expense
    net_change = p2_net - p1_net

    income_pct = ((p2_income - p1_income) / p1_income * 100) if p1_income != 0 else (100 if p2_income > 0 else 0)
    expense_pct = ((p2_expense - p1_expense) / p1_expense * 100) if p1_expense != 0 else (100 if p2_expense > 0 else 0)
    net_pct = ((p2_net - p1_net) / p1_net * 100) if p1_net != 0 else (100 if p2_net > 0 else 0)

    return {
        'period1': {
            **p1,
            'date_from': period1_from.isoformat(),
            'date_to': period1_to.isoformat(),
        },
        'period2': {
            **p2,
            'date_from': period2_from.isoformat(),
            'date_to': period2_to.isoformat(),
        },
        'change': {
            'income_change': str(income_change),
            'expense_change': str(expense_change),
            'net_change': str(net_change),
            'income_change_pct': str(income_pct),
            'expense_change_pct': str(expense_pct),
            'net_change_pct': str(net_pct),
        },
    }


def get_period_comparison(user, period1_from, period1_to, period2_from, period2_to):
    cache_key = build_finance_cache_key(
        'analytics:period_comparison',
        user.id,
        payload={
            'period1_from': period1_from,
            'period1_to': period1_to,
            'period2_from': period2_from,
            'period2_to': period2_to,
        },
    )
    return get_cached_finance_payload(
        cache_key,
        builder=lambda: _build_period_comparison(
            user,
            period1_from=period1_from,
            period1_to=period1_to,
            period2_from=period2_from,
            period2_to=period2_to,
        ),
        ttl=settings.FINANCE_CACHE_TTL,
    )
