import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(
        field_name='transaction_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='transaction_date',
        lookup_expr='lte'
    )

    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'category',
        ]
