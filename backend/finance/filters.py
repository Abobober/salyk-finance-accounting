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
    search = django_filters.CharFilter(
        method='filter_search',
        label='Поиск по описанию и сумме'
    )

    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'category',
            'is_business',
            'payment_method',
            'is_taxable',
            'activity_code',
        ]

    def filter_search(self, queryset, name, value):
        if not value or not value.strip():
            return queryset
        from django.db.models import Q
        v = value.strip()
        return queryset.filter(Q(description__icontains=v))

