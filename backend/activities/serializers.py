from rest_framework import serializers
from activities.models import ActivityCode


class ActivityCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения справочника видов деятельности."""
    class Meta:
        model = ActivityCode
        fields = ('id', 'code', 'section', 'name')
        read_only_fields = ('id', 'code', 'section', 'name')