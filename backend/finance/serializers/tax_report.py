"""Tax report response serializers for OpenAPI."""

from rest_framework import serializers


class TaxReportPeriodSerializer(serializers.Serializer):
    date_from = serializers.CharField()
    date_to = serializers.CharField()


class TaxReportTotalsSerializer(serializers.Serializer):
    total_income = serializers.CharField()
    total_expense = serializers.CharField()
    net = serializers.CharField()


class TaxReportByPaymentSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    payment_method_display = serializers.CharField()
    income = serializers.CharField()
    expense = serializers.CharField()
    net = serializers.CharField()


class TaxReportByActivitySerializer(serializers.Serializer):
    activity_code_id = serializers.IntegerField(allow_null=True)
    activity_name = serializers.CharField(allow_null=True)
    income = serializers.CharField()
    expense = serializers.CharField()
    net = serializers.CharField()


class TaxReportResponseSerializer(serializers.Serializer):
    period = TaxReportPeriodSerializer()
    totals = TaxReportTotalsSerializer()
    taxable = serializers.DictField()
    non_taxable = serializers.DictField()
    by_payment_method = TaxReportByPaymentSerializer(many=True)
    by_activity = TaxReportByActivitySerializer(many=True)
