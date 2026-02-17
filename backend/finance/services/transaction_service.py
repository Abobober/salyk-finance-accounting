from django.db import transaction
from finance.models import Transaction

class TransactionService:

    @staticmethod
    @transaction.atomic
    def create_transaction(user, validated_data):
        # тут можно добавить доп. бизнес-логику
        transaction_obj = Transaction.objects.create(
            user=user,
            **validated_data
        )

        # тут можно добавить:
        # - расчет налога
        # - обновление агрегатов
        # - логирование

        return transaction_obj
