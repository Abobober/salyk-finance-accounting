"""Category service layer."""

from django.db import transaction

from finance.models import Category
from finance.utils import update_instance_from_dict


class CategoryService:
    """Service for category operations."""

    @staticmethod
    @transaction.atomic
    def create_category(user, validated_data):
        """Create a new category."""
        return Category.objects.create(user=user, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_category(instance, validated_data):
        """Update an existing category."""
        return update_instance_from_dict(instance, validated_data)
