"""Tax report v2 response serializers for OpenAPI."""

from rest_framework import serializers


class TaxReportV2MetaSerializer(serializers.Serializer):
    schema_version = serializers.CharField()
    generated_at = serializers.CharField()
    currency = serializers.CharField()
    rate_precedence = serializers.CharField()


class TaxReportV2PeriodSerializer(serializers.Serializer):
    mode = serializers.CharField()
    preset = serializers.CharField(allow_null=True)
    date_from = serializers.CharField()
    date_to = serializers.CharField()


class TaxReportV2OrganizationActivitySerializer(serializers.Serializer):
    activity_id = serializers.IntegerField()
    activity_code = serializers.CharField()
    activity_name = serializers.CharField()
    is_primary = serializers.BooleanField()
    cash_tax_rate = serializers.CharField()
    non_cash_tax_rate = serializers.CharField()


class TaxReportV2OrganizationSnapshotSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    tax_regime = serializers.CharField(allow_null=True)
    tax_period_type = serializers.CharField(allow_null=True)
    tax_period_preset = serializers.CharField(allow_null=True)
    tax_period_custom_day = serializers.IntegerField(allow_null=True)
    activities = TaxReportV2OrganizationActivitySerializer(many=True)


class TaxReportV2SummarySerializer(serializers.Serializer):
    transaction_count = serializers.IntegerField()
    total_income = serializers.CharField()
    total_expense = serializers.CharField()
    net = serializers.CharField()
    taxable_income = serializers.CharField()
    taxable_expense = serializers.CharField()
    non_taxable_income = serializers.CharField()
    non_taxable_expense = serializers.CharField()
    total_tax_due = serializers.CharField()


class TaxReportV2ByPaymentMethodSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    payment_method_display = serializers.CharField()
    income = serializers.CharField()
    expense = serializers.CharField()
    taxable_income = serializers.CharField()
    taxable_expense = serializers.CharField()
    net = serializers.CharField()
    tax_due = serializers.CharField()


class TaxReportV2ByActivitySerializer(serializers.Serializer):
    activity_code_id = serializers.IntegerField(allow_null=True)
    activity_code = serializers.CharField(allow_null=True)
    activity_name = serializers.CharField(allow_null=True)
    is_primary = serializers.BooleanField()
    income = serializers.CharField()
    expense = serializers.CharField()
    taxable_income = serializers.CharField()
    taxable_expense = serializers.CharField()
    net = serializers.CharField()
    tax_due = serializers.CharField()


class TaxReportV2BreakdownsSerializer(serializers.Serializer):
    by_payment_method = TaxReportV2ByPaymentMethodSerializer(many=True)
    by_activity = TaxReportV2ByActivitySerializer(many=True)


class TaxReportV2CalculationItemSerializer(serializers.Serializer):
    activity_code_id = serializers.IntegerField(allow_null=True)
    activity_code = serializers.CharField(allow_null=True)
    activity_name = serializers.CharField(allow_null=True)
    payment_method = serializers.CharField()
    payment_method_display = serializers.CharField()
    applied_rate = serializers.CharField()
    rate_source = serializers.CharField()
    taxable_base = serializers.CharField()
    transaction_count = serializers.IntegerField()
    tax_due = serializers.CharField()


class TaxReportV2CalculationSerializer(serializers.Serializer):
    items = TaxReportV2CalculationItemSerializer(many=True)


class TaxReportV2WarningSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    count = serializers.IntegerField()


class TaxReportV2ResponseSerializer(serializers.Serializer):
    meta = TaxReportV2MetaSerializer()
    period = TaxReportV2PeriodSerializer()
    organization_snapshot = TaxReportV2OrganizationSnapshotSerializer()
    summary = TaxReportV2SummarySerializer()
    breakdowns = TaxReportV2BreakdownsSerializer()
    tax_calculation = TaxReportV2CalculationSerializer()
    warnings = TaxReportV2WarningSerializer(many=True)
