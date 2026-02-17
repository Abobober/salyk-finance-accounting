"""Dashboard response serializers for OpenAPI documentation."""

from rest_framework import serializers


class DashboardTotalsSerializer(serializers.Serializer):
    """Dashboard totals."""

    total_income = serializers.CharField()
    total_expense = serializers.CharField()


class DashboardCategorySerializer(serializers.Serializer):
    """Dashboard category breakdown item."""

    category_name = serializers.CharField()
    category_type = serializers.CharField()
    total = serializers.CharField()


class DashboardRecentTransactionSerializer(serializers.Serializer):
    """Dashboard recent transaction."""

    id = serializers.IntegerField()
    amount = serializers.CharField()
    transaction_type = serializers.CharField()
    category_name = serializers.CharField(allow_null=True)
    description = serializers.CharField()
    transaction_date = serializers.CharField()
    created_at = serializers.CharField()
    payment_method = serializers.CharField()


class DashboardResponseSerializer(serializers.Serializer):
    """Dashboard response structure."""

    totals = DashboardTotalsSerializer()
    by_category = DashboardCategorySerializer(many=True)
    recent_transactions = DashboardRecentTransactionSerializer(many=True)
