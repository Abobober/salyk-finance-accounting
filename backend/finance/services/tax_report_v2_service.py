"""Canonical tax report v2 service."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone

from finance.cache_utils import build_finance_cache_key, get_cached_finance_payload
from finance.constants import ZERO
from finance.models import Transaction
from finance.utils import get_preset_dates, parse_date_param
from organization.models import OrganizationActivity
from organization.services import get_or_create_organization_profile
from organization.tax_period_utils import get_current_tax_period_start_end


SUPPORTED_QUERY_PARAMS = frozenset({
    'use_org_tax_period',
    'preset',
    'date_from',
    'date_to',
    'format',
})
TRUE_VALUES = {'1', 'true', 'yes', 'on'}
TWO_PLACES = Decimal('0.01')
RATE_PRECEDENCE = 'transaction_snapshot_then_organization_activity'
SCHEMA_VERSION = '2.0'
CURRENCY = 'KGS'
WARNING_MESSAGES = {
    'missing_tax_rate': 'Taxable business income without any applicable tax rate was excluded from tax_due.',
    'non_business_taxable_income_excluded': 'Taxable non-business income was excluded from tax_due.',
}


class TaxReportV2ValidationError(Exception):
    """Raised when v2 report query params are invalid."""

    def __init__(self, detail: dict[str, str]):
        super().__init__(detail.get('error', 'Invalid tax report request.'))
        self.detail = detail


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _format_money(value: Decimal) -> str:
    return f'{_quantize_money(value):.2f}'


def _format_rate(value: Decimal) -> str:
    return f'{value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP):.2f}'


def _add_warning(warnings: dict[str, dict[str, object]], code: str) -> None:
    payload = warnings.setdefault(
        code,
        {
            'code': code,
            'message': WARNING_MESSAGES[code],
            'count': 0,
        },
    )
    payload['count'] += 1


def _normalized_bool(value: object) -> bool:
    return str(value or '').strip().lower() in TRUE_VALUES


def _resolve_all_time_dates(user) -> tuple:
    date_to = timezone.now().date()
    earliest = (
        Transaction.objects
        .filter(user=user)
        .order_by('transaction_date')
        .values_list('transaction_date', flat=True)
        .first()
    )
    if earliest and earliest <= date_to:
        return earliest, date_to
    return date_to, date_to


def _resolve_period(user, params) -> dict[str, object]:
    unsupported = sorted(key for key in params.keys() if key not in SUPPORTED_QUERY_PARAMS)
    if unsupported:
        raise TaxReportV2ValidationError({
            'error': (
                'Unsupported query params for tax-report v2: '
                f"{', '.join(unsupported)}. Only period selector params are allowed."
            )
        })

    use_org = _normalized_bool(params.get('use_org_tax_period'))
    preset = (params.get('preset') or '').strip()
    raw_date_from = params.get('date_from')
    raw_date_to = params.get('date_to')

    if use_org:
        profile = get_or_create_organization_profile(user)
        if not profile.tax_period_type:
            raise TaxReportV2ValidationError({
                'error': 'Tax period is not configured. Set it in organization profile before using use_org_tax_period=true.'
            })
        try:
            date_from, date_to = get_current_tax_period_start_end(profile)
        except ValueError as exc:
            raise TaxReportV2ValidationError({'error': str(exc)}) from exc
        return {
            'mode': 'org_tax_period',
            'preset': None,
            'date_from': date_from,
            'date_to': date_to,
        }

    has_preset = bool(preset)
    has_date_selector = bool(raw_date_from or raw_date_to)

    if has_preset and has_date_selector:
        raise TaxReportV2ValidationError({
            'error': 'Provide exactly one period selector: preset, date_from/date_to, or use_org_tax_period=true.'
        })

    if not has_preset and not has_date_selector:
        raise TaxReportV2ValidationError({
            'error': 'Provide exactly one period selector: preset, date_from/date_to, or use_org_tax_period=true.'
        })

    if has_preset:
        if preset == 'all_time':
            date_from, date_to = _resolve_all_time_dates(user)
        else:
            date_from, date_to = get_preset_dates(preset)
            if date_from is None or date_to is None:
                raise TaxReportV2ValidationError({
                    'error': f'Invalid preset: {preset}. Use: week, month, year, all_time'
                })

        return {
            'mode': 'preset',
            'preset': preset,
            'date_from': date_from,
            'date_to': date_to,
        }

    if not (raw_date_from and raw_date_to):
        raise TaxReportV2ValidationError({
            'error': 'Both date_from and date_to are required when using explicit dates.'
        })

    date_from, error = parse_date_param(raw_date_from, 'date_from')
    if error:
        raise TaxReportV2ValidationError(error)
    date_to, error = parse_date_param(raw_date_to, 'date_to')
    if error:
        raise TaxReportV2ValidationError(error)
    if date_from > date_to:
        raise TaxReportV2ValidationError({
            'error': 'date_from cannot be later than date_to.'
        })

    return {
        'mode': 'custom_dates',
        'preset': None,
        'date_from': date_from,
        'date_to': date_to,
    }


def _empty_payment_breakdown_row(method: str, label: str) -> dict[str, object]:
    return {
        'payment_method': method,
        'payment_method_display': label,
        'income': ZERO,
        'expense': ZERO,
        'taxable_income': ZERO,
        'taxable_expense': ZERO,
        'net': ZERO,
        'tax_due': ZERO,
    }


def _activity_identity(transaction, org_activity_map: dict[int, OrganizationActivity]) -> dict[str, object]:
    org_activity = org_activity_map.get(transaction.activity_code_id)
    activity = transaction.activity_code
    return {
        'activity_code_id': transaction.activity_code_id,
        'activity_code': activity.code if activity else None,
        'activity_name': activity.name if activity else None,
        'is_primary': bool(org_activity and org_activity.is_primary),
    }


def _ensure_activity_breakdown_row(
    activity_breakdowns: dict[object, dict[str, object]],
    transaction,
    org_activity_map: dict[int, OrganizationActivity],
) -> dict[str, object]:
    if transaction.activity_code_id not in activity_breakdowns:
        activity_breakdowns[transaction.activity_code_id] = {
            **_activity_identity(transaction, org_activity_map),
            'income': ZERO,
            'expense': ZERO,
            'taxable_income': ZERO,
            'taxable_expense': ZERO,
            'net': ZERO,
            'tax_due': ZERO,
        }
    return activity_breakdowns[transaction.activity_code_id]


def _resolve_transaction_rate(
    transaction,
    org_activity_map: dict[int, OrganizationActivity],
) -> tuple[Decimal | None, str | None]:
    snapshot_rate = (
        transaction.cash_tax_rate
        if transaction.payment_method == Transaction.PaymentMethod.CASH
        else transaction.non_cash_tax_rate
    )
    if snapshot_rate is not None:
        return snapshot_rate, 'transaction_snapshot'

    org_activity = org_activity_map.get(transaction.activity_code_id)
    if not org_activity:
        return None, None

    fallback_rate = (
        org_activity.cash_tax_rate
        if transaction.payment_method == Transaction.PaymentMethod.CASH
        else org_activity.non_cash_tax_rate
    )
    if fallback_rate is None:
        return None, None
    return fallback_rate, 'organization_activity'


def _build_tax_report_v2(user, resolved_period: dict[str, object]) -> dict[str, object]:
    profile = get_or_create_organization_profile(user)
    org_activities = list(
        OrganizationActivity.objects
        .filter(profile=profile)
        .select_related('activity')
        .order_by('-is_primary', 'activity__code', 'activity__name')
    )
    org_activity_map = {activity.activity_id: activity for activity in org_activities}

    date_from = resolved_period['date_from']
    date_to = resolved_period['date_to']

    transactions = list(
        Transaction.objects
        .filter(
            user=user,
            transaction_date__gte=date_from,
            transaction_date__lte=date_to,
        )
        .select_related('activity_code')
        .order_by('transaction_date', 'id')
    )

    summary = {
        'transaction_count': 0,
        'total_income': ZERO,
        'total_expense': ZERO,
        'net': ZERO,
        'taxable_income': ZERO,
        'taxable_expense': ZERO,
        'non_taxable_income': ZERO,
        'non_taxable_expense': ZERO,
        'total_tax_due': ZERO,
    }
    payment_breakdowns = {
        method: _empty_payment_breakdown_row(method, label)
        for method, label in Transaction.PaymentMethod.choices
    }
    activity_breakdowns: dict[object, dict[str, object]] = {}
    tax_items: dict[tuple[object, str, Decimal, str], dict[str, object]] = {}
    warnings: dict[str, dict[str, object]] = {}

    for transaction in transactions:
        amount = transaction.amount or ZERO
        is_income = transaction.transaction_type == Transaction.TransactionType.INCOME
        summary['transaction_count'] += 1

        if is_income:
            summary['total_income'] += amount
        else:
            summary['total_expense'] += amount

        payment_row = payment_breakdowns[transaction.payment_method]
        if is_income:
            payment_row['income'] += amount
        else:
            payment_row['expense'] += amount

        activity_row = None
        if transaction.activity_code_id is not None or transaction.is_business:
            activity_row = _ensure_activity_breakdown_row(activity_breakdowns, transaction, org_activity_map)
            if is_income:
                activity_row['income'] += amount
            else:
                activity_row['expense'] += amount

        if transaction.is_taxable:
            if is_income:
                summary['taxable_income'] += amount
                payment_row['taxable_income'] += amount
                if activity_row is not None:
                    activity_row['taxable_income'] += amount
            else:
                summary['taxable_expense'] += amount
                payment_row['taxable_expense'] += amount
                if activity_row is not None:
                    activity_row['taxable_expense'] += amount
        else:
            if is_income:
                summary['non_taxable_income'] += amount
            else:
                summary['non_taxable_expense'] += amount

        if not (transaction.is_taxable and is_income):
            continue

        if not transaction.is_business:
            _add_warning(warnings, 'non_business_taxable_income_excluded')
            continue

        applied_rate, rate_source = _resolve_transaction_rate(transaction, org_activity_map)
        if applied_rate is None or rate_source is None:
            _add_warning(warnings, 'missing_tax_rate')
            continue

        tax_due = _quantize_money(amount * applied_rate / Decimal('100'))
        summary['total_tax_due'] += tax_due
        payment_row['tax_due'] += tax_due
        if activity_row is not None:
            activity_row['tax_due'] += tax_due

        item_key = (
            transaction.activity_code_id,
            transaction.payment_method,
            applied_rate.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            rate_source,
        )
        item = tax_items.setdefault(
            item_key,
            {
                **_activity_identity(transaction, org_activity_map),
                'payment_method': transaction.payment_method,
                'payment_method_display': transaction.get_payment_method_display(),
                'applied_rate': item_key[2],
                'rate_source': rate_source,
                'taxable_base': ZERO,
                'transaction_count': 0,
                'tax_due': ZERO,
            },
        )
        item['taxable_base'] += amount
        item['transaction_count'] += 1
        item['tax_due'] += tax_due

    summary['net'] = summary['total_income'] - summary['total_expense']
    for row in payment_breakdowns.values():
        row['net'] = row['income'] - row['expense']
    for row in activity_breakdowns.values():
        row['net'] = row['income'] - row['expense']

    return {
        'meta': {
            'schema_version': SCHEMA_VERSION,
            'generated_at': timezone.now().isoformat(),
            'currency': CURRENCY,
            'rate_precedence': RATE_PRECEDENCE,
        },
        'period': {
            'mode': resolved_period['mode'],
            'preset': resolved_period['preset'],
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
        },
        'organization_snapshot': {
            'user_id': user.id,
            'tax_regime': profile.tax_regime,
            'tax_period_type': profile.tax_period_type,
            'tax_period_preset': profile.tax_period_preset,
            'tax_period_custom_day': profile.tax_period_custom_day,
            'activities': [
                {
                    'activity_id': org_activity.activity_id,
                    'activity_code': org_activity.activity.code,
                    'activity_name': org_activity.activity.name,
                    'is_primary': org_activity.is_primary,
                    'cash_tax_rate': _format_rate(org_activity.cash_tax_rate),
                    'non_cash_tax_rate': _format_rate(org_activity.non_cash_tax_rate),
                }
                for org_activity in org_activities
            ],
        },
        'summary': {
            'transaction_count': summary['transaction_count'],
            'total_income': _format_money(summary['total_income']),
            'total_expense': _format_money(summary['total_expense']),
            'net': _format_money(summary['net']),
            'taxable_income': _format_money(summary['taxable_income']),
            'taxable_expense': _format_money(summary['taxable_expense']),
            'non_taxable_income': _format_money(summary['non_taxable_income']),
            'non_taxable_expense': _format_money(summary['non_taxable_expense']),
            'total_tax_due': _format_money(summary['total_tax_due']),
        },
        'breakdowns': {
            'by_payment_method': [
                {
                    **{
                        key: row[key]
                        for key in ('payment_method', 'payment_method_display')
                    },
                    'income': _format_money(row['income']),
                    'expense': _format_money(row['expense']),
                    'taxable_income': _format_money(row['taxable_income']),
                    'taxable_expense': _format_money(row['taxable_expense']),
                    'net': _format_money(row['net']),
                    'tax_due': _format_money(row['tax_due']),
                }
                for method, _label in Transaction.PaymentMethod.choices
                for row in [payment_breakdowns[method]]
            ],
            'by_activity': [
                {
                    **{
                        key: row[key]
                        for key in ('activity_code_id', 'activity_code', 'activity_name', 'is_primary')
                    },
                    'income': _format_money(row['income']),
                    'expense': _format_money(row['expense']),
                    'taxable_income': _format_money(row['taxable_income']),
                    'taxable_expense': _format_money(row['taxable_expense']),
                    'net': _format_money(row['net']),
                    'tax_due': _format_money(row['tax_due']),
                }
                for row in sorted(
                    activity_breakdowns.values(),
                    key=lambda item: (
                        item['activity_code'] is None,
                        item['activity_code'] or '',
                        item['activity_name'] or '',
                    ),
                )
            ],
        },
        'tax_calculation': {
            'items': [
                {
                    **{
                        key: item[key]
                        for key in (
                            'activity_code_id',
                            'activity_code',
                            'activity_name',
                            'payment_method',
                            'payment_method_display',
                            'rate_source',
                        )
                    },
                    'applied_rate': _format_rate(item['applied_rate']),
                    'taxable_base': _format_money(item['taxable_base']),
                    'transaction_count': item['transaction_count'],
                    'tax_due': _format_money(item['tax_due']),
                }
                for item in sorted(
                    tax_items.values(),
                    key=lambda payload: (
                        payload['activity_code'] is None,
                        payload['activity_code'] or '',
                        payload['payment_method'],
                        payload['applied_rate'],
                        payload['rate_source'],
                    ),
                )
            ]
        },
        'warnings': [
            warnings[code]
            for code in WARNING_MESSAGES
            if code in warnings
        ],
    }


def build_tax_report_v2(user, params) -> dict[str, object]:
    resolved_period = _resolve_period(user, params)
    cache_key = build_finance_cache_key(
        'tax_report_v2',
        user.id,
        payload={
            'mode': resolved_period['mode'],
            'preset': resolved_period['preset'],
            'date_from': resolved_period['date_from'],
            'date_to': resolved_period['date_to'],
        },
    )
    return get_cached_finance_payload(
        cache_key,
        builder=lambda: _build_tax_report_v2(user, resolved_period),
        ttl=settings.FINANCE_CACHE_TTL,
    )
