from django.db import transaction
from rest_framework import serializers

from finance.models import Transaction
from finance.utils import update_instance_from_dict


def _validate_transaction_business_rules(validated_data, instance=None):
    """Validate business rules: category type match and activity_code for business transactions."""
    category = validated_data.get("category") if "category" in validated_data else (
        instance.category if instance else None
    )
    t_type = validated_data.get("transaction_type") if "transaction_type" in validated_data else (
        instance.transaction_type if instance else None
    )
    is_business = validated_data.get("is_business") if "is_business" in validated_data else (
        instance.is_business if instance else True
    )
    activity_code = validated_data.get("activity_code") if "activity_code" in validated_data else (
        instance.activity_code if instance else None
    )

    if category and t_type and category.category_type != t_type:
        raise serializers.ValidationError({
            "category": f"Тип категории ({category.get_category_type_display()}) не совпадает с типом операции ({t_type})"
        })
    if is_business and not activity_code:
        raise serializers.ValidationError({
            "activity_code": "Для бизнес-транзакции необходимо указать вид деятельности."
        })


class TransactionService:
    """Service for transaction operations: business rules + atomicity."""

    @staticmethod
    @transaction.atomic
    def create_transaction(user, validated_data):
        """Create a new transaction."""
        _validate_transaction_business_rules(validated_data, instance=None)
        return Transaction.objects.create(user=user, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_transaction(instance, validated_data):
        """Update an existing transaction."""
        _validate_transaction_business_rules(validated_data, instance=instance)
        update_instance_from_dict(instance, validated_data)
        return instance
