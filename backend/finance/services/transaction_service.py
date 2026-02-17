from django.db import transaction
from rest_framework import serializers

from finance.models import Transaction
from finance.services.dashboard_service import invalidate_dashboard_cache


def _validate_transaction_business_rules(validated_data, instance=None):
    """Stage 2: business rules (category type match, activity_code for business)."""
    category = validated_data.get("category") if "category" in validated_data else (instance.category if instance else None)
    t_type = validated_data.get("transaction_type") if "transaction_type" in validated_data else (instance.transaction_type if instance else None)
    is_business = validated_data.get("is_business") if "is_business" in validated_data else (instance.is_business if instance else True)
    activity_code = validated_data.get("activity_code") if "activity_code" in validated_data else (instance.activity_code if instance else None)

    if category and t_type and category.category_type != t_type:
        raise serializers.ValidationError({
            "category": f"Тип категории ({category.get_category_type_display()}) не совпадает с типом операции ({t_type})"
        })
    if is_business and not activity_code:
        raise serializers.ValidationError({
            "activity_code": "Для бизнес-транзакции необходимо указать вид деятельности."
        })


class TransactionService:
    """
    Service layer: business rules + atomicity. Amount validation lives in serializer + model only.
    """

    @staticmethod
    @transaction.atomic
    def create_transaction(user, validated_data):
        _validate_transaction_business_rules(validated_data, instance=None)
        obj = Transaction.objects.create(user=user, **validated_data)
        invalidate_dashboard_cache(user)
        return obj

    @staticmethod
    @transaction.atomic
    def update_transaction(instance, validated_data):
        _validate_transaction_business_rules(validated_data, instance=instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        invalidate_dashboard_cache(instance.user)
        return instance
