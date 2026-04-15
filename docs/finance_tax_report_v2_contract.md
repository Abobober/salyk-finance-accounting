# Finance Tax Report V2 Contract

Canonical contract for downstream consumers of the main financial backend:
- frontend
- PDF/report generation module
- AI/report explanation module

This document describes the **current** backend contract implemented by:
- `GET /api/finance/tax-report/v2/`

It is the recommended source of truth for financial tax-report data.
Downstream modules should consume this payload instead of recalculating tax logic locally.

## Ownership Boundary

The main financial backend is responsible for:
- period resolution
- transaction aggregation
- tax-rate resolution
- tax calculation
- zero-safe response structure
- warnings about incomplete or excluded tax-calculation cases

Other modules must treat `v2` as a data contract, not as a suggestion to re-implement report logic.

## Endpoint

`GET /api/finance/tax-report/v2/`

Auth:
- JWT Bearer token
- onboarding must be completed

Base path:
- `/api/finance/tax-report/v2/`

## Query Parameters

Exactly one period selector must be provided.

Supported selectors:
- `use_org_tax_period=true`
- `preset=week|month|year|all_time`
- `date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`

Allowed extra param:
- `format`
  Used only by DRF/OpenAPI tooling. Consumers must not rely on it.

### Validation Rules

- If `use_org_tax_period=true`, the backend ignores `preset`, `date_from`, and `date_to`.
- If no period selector is provided, backend returns `400`.
- If more than one period selector is mixed, backend returns `400`.
- If only one of `date_from` or `date_to` is provided, backend returns `400`.
- If `date_from > date_to`, backend returns `400`.
- Any non-period financial filters such as `category`, `activity_code`, `payment_method`, `is_taxable`, `search`, etc. are rejected with `400`.

This is intentional: `v2` is a canonical report endpoint, not a UI-filtered slice.

## High-Level Behavior

- The report is built only from transactions of the authenticated user.
- All money values are returned as decimal strings with 2 digits after the decimal point.
- Empty periods return `200 OK` and a full zero-safe structure.
- `by_payment_method` always contains both `cash` and `non_cash` rows.
- `by_activity` contains only activities that appear in period transactions.
- `tax_calculation.items` contains only rows that actually contributed to tax calculation.
- In this phase, tax due is calculated only from **taxable business income**.
- Expenses are reported in summaries and breakdowns, but do not reduce `tax_due`.
- Taxable non-business income is reported in totals, but excluded from `tax_due` and surfaced in `warnings`.

## Rate Resolution Rules

Rate precedence is fixed:

1. transaction snapshot rate
   - `cash_tax_rate` for `payment_method=cash`
   - `non_cash_tax_rate` for `payment_method=non_cash`
2. fallback to current `OrganizationActivity` rate
3. if still missing, transaction is excluded from `tax_due` and a warning is emitted

The backend exposes this policy in:
- `meta.rate_precedence = "transaction_snapshot_then_organization_activity"`

## Response Shape

```json
{
  "meta": {
    "schema_version": "2.0",
    "generated_at": "2026-04-15T12:34:56.000000+06:00",
    "currency": "KGS",
    "rate_precedence": "transaction_snapshot_then_organization_activity"
  },
  "period": {
    "mode": "preset | custom_dates | org_tax_period",
    "preset": "week | month | year | all_time | null",
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD"
  },
  "organization_snapshot": {
    "user_id": 1,
    "tax_regime": "single | general | null",
    "tax_period_type": "preset | custom | null",
    "tax_period_preset": "monthly | quarterly | yearly | null",
    "tax_period_custom_day": 1,
    "activities": [
      {
        "activity_id": 10,
        "activity_code": "A01",
        "activity_name": "Retail trade",
        "is_primary": true,
        "cash_tax_rate": "3.00",
        "non_cash_tax_rate": "2.00"
      }
    ]
  },
  "summary": {
    "transaction_count": 6,
    "total_income": "380.00",
    "total_expense": "50.00",
    "net": "330.00",
    "taxable_income": "330.00",
    "taxable_expense": "40.00",
    "non_taxable_income": "50.00",
    "non_taxable_expense": "10.00",
    "total_tax_due": "13.00"
  },
  "breakdowns": {
    "by_payment_method": [
      {
        "payment_method": "cash",
        "payment_method_display": "Cash",
        "income": "180.00",
        "expense": "40.00",
        "taxable_income": "130.00",
        "taxable_expense": "40.00",
        "net": "140.00",
        "tax_due": "3.00"
      }
    ],
    "by_activity": [
      {
        "activity_code_id": 10,
        "activity_code": "A01",
        "activity_name": "Retail trade",
        "is_primary": true,
        "income": "150.00",
        "expense": "40.00",
        "taxable_income": "100.00",
        "taxable_expense": "40.00",
        "net": "110.00",
        "tax_due": "3.00"
      }
    ]
  },
  "tax_calculation": {
    "items": [
      {
        "activity_code_id": 10,
        "activity_code": "A01",
        "activity_name": "Retail trade",
        "payment_method": "cash",
        "payment_method_display": "Cash",
        "applied_rate": "3.00",
        "rate_source": "transaction_snapshot | organization_activity",
        "taxable_base": "100.00",
        "transaction_count": 1,
        "tax_due": "3.00"
      }
    ]
  },
  "warnings": [
    {
      "code": "non_business_taxable_income_excluded",
      "message": "Taxable non-business income was excluded from tax_due.",
      "count": 1
    }
  ]
}
```

## Field Semantics

### `meta`

- `schema_version`
  Contract version of the response payload.
- `generated_at`
  Time when backend generated the report payload.
- `currency`
  Current reporting currency. At the moment always `KGS`.
- `rate_precedence`
  Human-readable backend rule for rate resolution.

### `period`

- `mode`
  How the period was selected:
  - `preset`
  - `custom_dates`
  - `org_tax_period`
- `preset`
  Present only for preset mode, otherwise `null`.
- `date_from`, `date_to`
  Final resolved inclusive period boundaries used by the backend.

Consumers must use resolved `date_from` and `date_to` as the official report period.

### `organization_snapshot`

This is the organization configuration **at report generation time**, not a historical snapshot table.

Use it for:
- display context
- PDF headers/metadata
- AI context

Do not use it to override transaction-level rate decisions already reflected in `tax_calculation`.

### `summary`

- `transaction_count`
  Number of transactions included in the period.
- `total_income`, `total_expense`, `net`
  Raw financial totals for the period.
- `taxable_*`, `non_taxable_*`
  Financial totals by taxability flag.
- `total_tax_due`
  Final calculated tax due for this phase.

Consumers must treat `summary.total_tax_due` as authoritative and must not re-sum from raw transactions independently.

### `breakdowns.by_payment_method`

Always contains:
- one row for `cash`
- one row for `non_cash`

`tax_due` here is the share of total tax attributable to taxable business income in that payment method.

### `breakdowns.by_activity`

Contains only activities found in the selected period’s transactions.

Notes:
- an activity may exist in `organization_snapshot.activities` but not appear here if there were no transactions for it in the period
- `is_primary` is taken from current organization activity configuration

### `tax_calculation.items`

Each item is grouped by:
- `activity_code_id`
- `payment_method`
- `applied_rate`
- `rate_source`

This means multiple groups for the same activity are possible if:
- payment method differs
- rate source differs
- applied rate differs

This block is the best source for:
- PDF line items
- AI explanations of why tax due has a given value

### `warnings`

Warnings are aggregated, not per-transaction.

Current warning codes:
- `missing_tax_rate`
  Taxable business income existed, but neither transaction snapshot nor organization activity rate could be resolved.
- `non_business_taxable_income_excluded`
  Taxable non-business income existed, but current backend scope excludes it from `tax_due`.

Consumers should show warnings when appropriate, but warnings do not make the response invalid.

## Zero-Period Contract

If there are no transactions in the selected period:
- backend returns `200`
- all `summary` amounts are `"0.00"`
- `transaction_count = 0`
- `breakdowns.by_payment_method` still contains both payment-method rows with zero values
- `breakdowns.by_activity = []`
- `tax_calculation.items = []`
- `warnings = []`

Consumers must handle this as a normal report, not as an error state.

## Error Contract

Validation errors return `400`:

```json
{
  "error": "Provide exactly one period selector: preset, date_from/date_to, or use_org_tax_period=true."
}
```

Common causes:
- no period selector
- mixed period selectors
- missing `date_from` or `date_to`
- invalid date format
- `date_from` later than `date_to`
- unsupported extra query params
- `use_org_tax_period=true` when org tax period is not configured

## Consumer Rules

### Frontend

- Use `summary`, `breakdowns`, and `warnings` directly.
- Do not locally recompute `total_tax_due`.
- Display resolved `period.date_from/date_to`, not raw query params.
- Treat empty period as a valid zero report.

### PDF/Export Module

- Use backend-resolved period and backend-computed totals.
- Use `organization_snapshot` for organization metadata.
- Use `tax_calculation.items` for line-item style export when needed.
- Do not apply separate tax formulas on top of this payload unless a new backend contract explicitly requires it.

### AI Module

- Use the entire response payload as structured context.
- Prefer `summary`, `tax_calculation.items`, and `warnings` for explanation.
- Do not infer different tax totals than backend `summary.total_tax_due`.

## Compatibility Notes

- The old endpoint `/api/finance/tax-report/` still exists for compatibility.
- New downstream work should use `/api/finance/tax-report/v2/`.
- `v2` is the canonical contract for new integrations.

## Current Limitations

- No PDF-specific field mapping is included in this phase.
- No AI-specific prompt payload is included in this phase.
- No regime-specific deduction logic beyond taxable business income tax calculation is implemented in this phase.
- `all_time` resolves to:
  - earliest user transaction date if one exists
  - otherwise current date for both `date_from` and `date_to`
