"""Analytics response serializers for OpenAPI documentation."""

from rest_framework import serializers


class TimeSeriesDataSerializer(serializers.Serializer):
    """Time series data point."""

    period = serializers.CharField()
    income = serializers.CharField()
    expense = serializers.CharField()
    net = serializers.CharField()


class TimeSeriesResponseSerializer(serializers.Serializer):
    """Time series analytics response."""

    period = serializers.CharField()
    preset = serializers.CharField(required=False, allow_null=True)
    date_from = serializers.CharField(required=False, allow_null=True)
    date_to = serializers.CharField(required=False, allow_null=True)
    data = TimeSeriesDataSerializer(many=True)


class CategoryBreakdownItemSerializer(serializers.Serializer):
    """Category breakdown item."""

    category_name = serializers.CharField()
    category_type = serializers.CharField()
    total = serializers.CharField()
    count = serializers.IntegerField()


class CategoryBreakdownResponseSerializer(serializers.Serializer):
    """Category breakdown analytics response."""

    preset = serializers.CharField(required=False, allow_null=True)
    date_from = serializers.CharField(required=False, allow_null=True)
    date_to = serializers.CharField(required=False, allow_null=True)
    transaction_type = serializers.CharField(required=False, allow_null=True)
    data = CategoryBreakdownItemSerializer(many=True)


class PeriodStatsSerializer(serializers.Serializer):
    """Period statistics."""

    income = serializers.CharField()
    expense = serializers.CharField()
    net = serializers.CharField()
    transaction_count = serializers.IntegerField()
    date_from = serializers.CharField()
    date_to = serializers.CharField()


class PeriodChangeSerializer(serializers.Serializer):
    """Period comparison change metrics."""

    income_change = serializers.CharField()
    expense_change = serializers.CharField()
    net_change = serializers.CharField()
    income_change_pct = serializers.CharField()
    expense_change_pct = serializers.CharField()
    net_change_pct = serializers.CharField()


class PeriodComparisonResponseSerializer(serializers.Serializer):
    """Period comparison analytics response."""

    period1 = PeriodStatsSerializer()
    period2 = PeriodStatsSerializer()
    change = PeriodChangeSerializer()
