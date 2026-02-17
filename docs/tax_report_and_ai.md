# Tax Report: What Exists vs AI Report Generation

## Does the current code block AI-based tax report generation?

**No.** The current code only provides **structured data** for a period. An AI agent can use that data (or the same underlying models) to generate narrative reports, PDFs, or other outputs without any conflict.

---

## What the current code DOES

### 1. Tax period (organization app)

- **Stores** on `OrganizationProfile`: `tax_period_type` (preset/custom), `tax_period_preset` (monthly/quarterly/yearly), `tax_period_custom_day` (1–31).
- **Computes** current period dates: `get_current_tax_period_start_end(profile)` → `(date_from, date_to)`.
- **Exposes** `GET /api/organization/tax-period/` → current period + next period start.
- **No AI.** Pure date math and settings.

### 2. Tax report data (finance app)

- **Service:** `build_tax_report(user, date_from, date_to)`  
  - Filters `Transaction` by user and `transaction_date` in `[date_from, date_to]`.  
  - Returns a **dict** (no PDF, no narrative):
    - `period`: `date_from`, `date_to`
    - `totals`: `total_income`, `total_expense`, `net`
    - `taxable` / `non_taxable`: income and expense
    - `by_payment_method`: cash/non_cash breakdown (income, expense, net)
    - `by_activity`: per activity code (income, expense, net) for business transactions
- **Endpoint:** `GET /api/finance/tax-report/`  
  - Query: `date_from` & `date_to`, or `preset=week|month|year|all_time`, or `use_org_tax_period=true`.  
  - Returns the same dict as JSON.
- **No AI.** Synchronous, read-only aggregation from `Transaction` (and existing org/profile data).

### 3. Data available for any consumer (including AI)

- **Models:** `Transaction` (amounts, dates, type, category, payment_method, is_taxable, activity_code, cash_tax_rate, non_cash_tax_rate), `OrganizationProfile` (tax period settings), `OrganizationActivity` (rates per activity).
- **Reusable:**  
  - Period: `organization.tax_period_utils.get_current_tax_period_start_end(profile)`.  
  - Report payload: `finance.services.tax_report_service.build_tax_report(user, date_from, date_to)` (callable from anywhere, no HTTP required).

---

## What the current code DOES NOT do

- **Does NOT** generate narrative text (e.g. “Your income in this period was …”).
- **Does NOT** produce PDFs or other document formats.
- **Does NOT** call any LLM or AI.
- **Does NOT** store or version “reports” (no `TaxReport` model or file storage).
- **Does NOT** define a single “report generation” pipeline that would force one implementation.
- **Does NOT** lock how report data is used: the payload is plain dict/JSON; anyone can take it and feed it to an agent, template, or PDF generator.

---

## How the other dev can add AI report generation

1. **Use existing data**
   - Get period: `get_current_tax_period_start_end(profile)` or any custom dates.
   - Get payload: `build_tax_report(user, date_from, date_to)` or query `Transaction` (and related) directly.
2. **Use existing endpoint**
   - Call `GET /api/finance/tax-report/?use_org_tax_period=true` (or with dates) and pass the JSON to an AI agent.
3. **Add new flow**
   - New endpoint(s), e.g. `POST /api/finance/tax-report/generate/` with `period` or `date_from`/`date_to`.
   - Backend: same data (service or API) → prompt + LLM → narrative/PDF or structured AI output.
   - Optional: Celery task, store result in a new model or file, etc.

No changes to the existing tax report or tax period code are required for that; it stays the “data layer” for any kind of report (human-readable API or AI-generated).

---

## Summary

| Concern | Answer |
|--------|--------|
| Does current code block AI report generation? | No. |
| Can AI use the same period logic? | Yes (`tax_period_utils`). |
| Can AI use the same report data? | Yes (service or HTTP). |
| Is there a “report format” that AI must follow? | No; current API is data-only. |
| Do we need to change existing code for AI? | No; add new endpoints/tasks that consume existing data. |
