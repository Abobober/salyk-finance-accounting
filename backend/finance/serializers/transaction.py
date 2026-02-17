"""Transaction serializers."""

from decimal import Decimal

from django.db.models import Q
from rest_framework import serializers

from activities.models import ActivityCode

from finance.constants import MAX_TRANSACTION_AMOUNT, MIN_TRANSACTION_AMOUNT
from finance.models import Category, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer with validation and dynamic querysets."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    activity_code_name = serializers.CharField(source='activity_code.name', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'amount', 'transaction_type', 'category', 'category_name',
            'description', 'transaction_date', 'created_at', 'payment_method',
            'is_business', 'is_taxable', 'activity_code', 'activity_code_name',
            'cash_tax_rate', 'non_cash_tax_rate'
        )
        read_only_fields = ('id', 'created_at', 'activity_code_name', 'cash_tax_rate', 'non_cash_tax_rate')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            user = request.user
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=user) | Q(is_system=True)
            )
            self.fields['activity_code'].queryset = ActivityCode.objects.filter(
                organizationactivity__profile=user.organization
            ).distinct()
        else:
            self.fields['category'].queryset = Category.objects.filter(is_system=True)

    def validate_amount(self, value):
        """Validate amount: must be positive and within limits."""
        if value is not None:
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            if value < MIN_TRANSACTION_AMOUNT:
                raise serializers.ValidationError("Сумма должна быть положительной.")
            if value > MAX_TRANSACTION_AMOUNT:
                raise serializers.ValidationError("Сумма превышает допустимый предел.")
        return value
