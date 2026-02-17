"""Analytics service for graphs: time series, category breakdown, period comparisons."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from finance.constants import (
    DATE_FORMAT,
    DEFAULT_ANALYTICS_DAYS,
    DEFAULT_CATEGORY_BREAKDOWN_LIMIT,
    MONTH_FORMAT,
    YEAR_FORMAT,
    ZERO,
)
from finance.models import Transaction


def get_time_series_data(user, period='monthly', date_from=None, date_to=None, transaction_type=None):
    """
    Time series data for charts (income/expense over time).
    
    Args:
        user: User instance
        period: 'daily', 'monthly', 'yearly'
        date_from: start date (default: 1 year ago)
        date_to: end date (default: today)
        transaction_type: 'income', 'expense', or None (both)
    
    Returns:
        List of {period: str, income: Decimal, expense: Decimal, net: Decimal}
    """
    base_qs = Transaction.objects.filter(user=user)
    
    if date_from:
        base_qs = base_qs.filter(transaction_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(transaction_date__lte=date_to)
    if transaction_type:
        base_qs = base_qs.filter(transaction_type=transaction_type)
    
    # Default: last N days if no dates provided
    if not date_from and not date_to:
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=DEFAULT_ANALYTICS_DAYS)
        base_qs = base_qs.filter(transaction_date__gte=date_from, transaction_date__lte=date_to)
    
    # Group by period
    period_configs = {
        'daily': ('transaction_date', DATE_FORMAT),
        'monthly': ('month', MONTH_FORMAT),
        'yearly': ('year', YEAR_FORMAT),
    }
    date_trunc, date_format = period_configs.get(period, ('month', MONTH_FORMAT))
    
    # Aggregate by period
    if date_trunc == 'transaction_date':
        # Daily: group by exact date
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
    else:
        # Monthly/Yearly: use Django's TruncMonth/TruncYear
        if date_trunc == 'month':
            qs = base_qs.annotate(
                period=TruncMonth('transaction_date')
            ).values('period').annotate(
                income=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.INCOME), default=0),
                expense=Sum('amount', filter=Q(transaction_type=Transaction.TransactionType.EXPENSE), default=0),
            ).order_by('period')
        else:  # yearly
            qs = base_qs.annotate(
                period=TruncYear('transaction_date')
            ).values('period').annotate(
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


def get_category_breakdown(user, date_from=None, date_to=None, transaction_type=None, limit=DEFAULT_CATEGORY_BREAKDOWN_LIMIT):
    """
    Category breakdown for a period (pie/bar chart data).
    
    Args:
        user: User instance
        date_from: start date
        date_to: end date
        transaction_type: 'income', 'expense', or None (both)
        limit: max categories to return (default: 10)
    
    Returns:
        List of {category_name: str, category_type: str, total: Decimal, count: int}
    """
    base_qs = Transaction.objects.filter(user=user)
    
    if date_from:
        base_qs = base_qs.filter(transaction_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(transaction_date__lte=date_to)
    if transaction_type:
        base_qs = base_qs.filter(transaction_type=transaction_type)
    
    qs = (
        base_qs.values('category__name', 'category__category_type')
        .annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        .filter(category__name__isnull=False)
        .order_by('-total')[:limit]
    )
    
    result = []
    for row in qs:
        result.append({
            'category_name': row['category__name'],
            'category_type': row['category__category_type'],
            'total': str(row['total'] or ZERO),
            'count': row['count'],
        })
    
    return result


def get_period_comparison(user, period1_from, period1_to, period2_from, period2_to):
    """
    Compare two periods (e.g., this month vs last month).
    
    Returns:
        {
            period1: {income, expense, net, transaction_count},
            period2: {income, expense, net, transaction_count},
            change: {income_change, expense_change, net_change, income_pct, expense_pct, net_pct}
        }
    """
    def get_period_stats(date_from, date_to):
        qs = Transaction.objects.filter(
            user=user,
            transaction_date__gte=date_from,
            transaction_date__lte=date_to
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
    
    # Calculate changes
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
