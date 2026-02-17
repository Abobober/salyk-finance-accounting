from rest_framework import serializers

class UnifiedTaxRequestSerializer(serializers.Serializer):
    year = serializers.IntegerField(required=True, min_value=2000, max_value=2100)
    quarter = serializers.ChoiceField(choices=[1,2,3,4], required=True)


class UnifiedTaxReportResponseSerializer(serializers.Serializer):
    report_data = serializers.DictField()
    pdf_file = serializers.URLField()
    ai_validation = serializers.CharField()
