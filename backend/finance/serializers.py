from rest_framework import serializers
from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    category_type = serializers.CharField(source='type')  # rename it here

    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'category_type',
            'is_system',
            'created_at',
        )
        read_only_fields = ('id', 'is_system', 'created_at')


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            'id',
            'amount',
            'transaction_type',
            'category',
            'category_name',
            'description',
            'transaction_date',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')
