"""Reusable transaction queryset filtering helpers."""

from __future__ import annotations

from collections.abc import Mapping

from django.db.models import QuerySet

from finance.models import Transaction


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None

    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def apply_transaction_query_filters(
    queryset: QuerySet[Transaction],
    params: Mapping[str, object] | None = None,
) -> QuerySet[Transaction]:
    """
    Apply the same transaction filters used by the list endpoint to any queryset.

    Accepts query-param-like mappings so dashboard/analytics/tax reports can stay
    in sync with the transaction table filters.
    """
    if not params:
        return queryset

    transaction_type = params.get("transaction_type")
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)

    category = params.get("category")
    if category not in (None, ""):
        queryset = queryset.filter(category_id=category)

    payment_method = params.get("payment_method")
    if payment_method:
        queryset = queryset.filter(payment_method=payment_method)

    activity_code = params.get("activity_code")
    if activity_code not in (None, ""):
        queryset = queryset.filter(activity_code_id=activity_code)

    is_business = _parse_bool(params.get("is_business"))
    if is_business is not None:
        queryset = queryset.filter(is_business=is_business)

    is_taxable = _parse_bool(params.get("is_taxable"))
    if is_taxable is not None:
        queryset = queryset.filter(is_taxable=is_taxable)

    date_from = params.get("date_from")
    if date_from:
        queryset = queryset.filter(transaction_date__gte=date_from)

    date_to = params.get("date_to")
    if date_to:
        queryset = queryset.filter(transaction_date__lte=date_to)

    search = str(params.get("search", "")).strip()
    if search:
        queryset = queryset.filter(description__icontains=search)

    return queryset
