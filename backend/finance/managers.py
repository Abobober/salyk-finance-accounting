"""Queryset managers for finance models."""

from django.db import models


class ActiveTransactionManager(models.Manager):
    """Исключает записи с мягким удалением (deleted_at заполнен)."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
