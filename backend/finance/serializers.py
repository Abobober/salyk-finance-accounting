from decimal import Decimal

from rest_framework import serializers
from django.db.models import Q

from .models import Category, Transaction
from activities.models import ActivityCode


class CategorySerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'category_type', 'category_type_display', 'is_system', 'created_at')
        read_only_fields = ('id', 'is_system', 'created_at')


class TransactionSerializer(serializers.ModelSerializer):
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
        """Stage 1.1: no negative or zero amounts; use Decimal."""
        if value is not None:
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            if value <= 0:
                raise serializers.ValidationError("Сумма должна быть положительной.")
            if value > Decimal("1000000000"):
                raise serializers.ValidationError("Сумма превышает допустимый предел.")
        return value

    def validate(self, attrs):
        # Stage 2: business rules (category type match, activity_code for business) live in TransactionService
        return attrs
