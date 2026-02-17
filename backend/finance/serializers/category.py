"""Category serializers."""

from rest_framework import serializers

from finance.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with display field."""

    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'category_type', 'category_type_display', 'is_system', 'created_at')
        read_only_fields = ('id', 'is_system', 'created_at')
