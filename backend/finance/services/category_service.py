"""Stage 2: Category service layer. View → service, serializer → validation only."""

from django.db import transaction

from finance.models import Category


class CategoryService:
    @staticmethod
    @transaction.atomic
    def create_category(user, validated_data):
        return Category.objects.create(user=user, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_category(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
