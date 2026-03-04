### Tax report template config (short)

- **API**: `get_template_path(report_type: str, tax_regime: str, period_key: str) -> Path`
- **Behavior**:
  - Returns absolute path to `form.pdf` or raises `TemplateNotFoundError` (use as 400, not 500).
  - Views/services **must not** build paths to `FORMS` directly.
- **Parameters**:
  - `report_type`: logical type (e.g. `unified_tax`) **or** form code (`STI-107`, `STI_107` → `STI-107`).
  - `tax_regime`: from `OrganizationProfile.tax_regime` (e.g. `single`, `general`).
  - `period_key`: logical period (e.g. `quarterly`) **or** version key (`_03`, `_06`, `_07`).
- **Resolution order**:
  1. Explicit map: `TAX_REPORT_TEMPLATES[report_type][tax_regime][period_key]`.
  2. Fallback: auto map `AVAILABLE_FORMS[form_code][version]` from `FORMS/**/form.pdf`:
     - Normalize `report_type` → form code.
     - If `period_key` matches version key, use it; otherwise use latest (`_NN`) by name.