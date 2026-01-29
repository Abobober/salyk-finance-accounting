from typing import Any, Dict

from rest_framework import serializers
from .models import Transaction, Category
from decimal import Decimal
from django.db.models import Q



class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий.
    Преобразует объект Category в JSON и обратно.
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'is_system', 'created_at']
        read_only_fields = ['id', 'is_system', 'created_at']
    
    def create(self, validated_data):
        """
        При создании категории автоматически привязываем ее к текущему пользователю.
        """
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),  # будет настроено в __init__
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )

    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'transaction_type_display',
            'category',
            'category_id',
            'amount',
            'description',
            'transaction_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем queryset для category_id — только системные или принадлежащие текущему пользователю
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category_id'].queryset = Category.objects.filter(
                Q(user=request.user) | Q(is_system=True)
            )

    def validate_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value

    def validate(self, data):
        # получаем transaction_type — сначала из входящих данных, затем (для update) из instance
        transaction_type = data.get('transaction_type') or (self.instance.transaction_type if self.instance else None)
        category = data.get('category') or (self.instance.category if self.instance else None)

        # Если есть категория — проверим соответствие типов
        if category and transaction_type and category.category_type != transaction_type:
            raise serializers.ValidationError({
                "category": f"Категория '{category.name}' предназначена для {category.get_category_type_display()}, а не для {dict(Transaction.TRANSACTION_TYPES).get(transaction_type)}"
            })

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class TransactionSummarySerializer(serializers.Serializer):
    """
    Сериализатор для сводки по транзакциям.
    Используется для отображения итогов.
    """
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    period = serializers.DictField(child=serializers.DateField(), read_only=True)
