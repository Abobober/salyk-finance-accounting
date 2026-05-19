import os
import json
import logging
from typing import List

import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)

# ensure we run import only once per process
_ran = False


def _parse_dataframe(df: pd.DataFrame) -> List[dict]:
    header_candidates = {
        'код', 'наименование', 'code', 'name', 'tax_office_code', 'tax_office_name',
        'tax office code', 'tax office name', 'tax_office', 'tax office'
    }

    offices = []
    for _, row in df.iterrows():
        code = ''
        name = ''
        try:
            v0 = row.iloc[0]
            if pd.notna(v0):
                code = str(v0).strip()
        except Exception:
            code = ''
        try:
            v1 = row.iloc[1]
            if pd.notna(v1):
                name = str(v1).strip()
        except Exception:
            name = ''

        if not code and not name:
            continue

        if (code or '').lower() in header_candidates or (name or '').lower() in header_candidates:
            continue

        offices.append({'code': code, 'name': name})

    # deduplicate by code
    seen = set()
    deduped = []
    for o in offices:
        c = (o.get('code') or '').strip()
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)
        deduped.append(o)

    return deduped


def try_autoload():
    global _ran
    if _ran:
        return
    _ran = True

    base_dir = getattr(settings, 'BASE_DIR', None)
    if base_dir is None:
        base_dir = os.getcwd()
    else:
        base_dir = str(base_dir)

    candidates = [
        os.path.join(base_dir, 'tax_org.xlsx'),
        os.path.join(base_dir, 'tax_org.xls'),
        os.path.join(base_dir, 'backend', 'organization', 'tax_org.xlsx'),
        os.path.join(base_dir, 'backend', 'organization', 'data', 'tax_org.xlsx'),
        os.path.join(base_dir, 'backend', 'organization', 'data', 'tax_org.xls'),
    ]

    excel_path = None
    for p in candidates:
        if os.path.exists(p):
            excel_path = p
            break

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'tax_offices.json')

    if not excel_path:
        # nothing to import
        return

    try:
        if os.path.exists(output_path) and os.path.getmtime(output_path) >= os.path.getmtime(excel_path):
            # up-to-date
            return
    except Exception:
        pass

    try:
        df = pd.read_excel(excel_path, header=None, engine='openpyxl', dtype=str)
        deduped = _parse_dataframe(df)
        with open(output_path, 'w', encoding='utf-8') as fh:
            json.dump(deduped, fh, ensure_ascii=False, indent=2)
        logger.info('Autoloaded %d tax offices from %s', len(deduped), excel_path)
    except Exception as exc:
        logger.exception('Failed to autoload tax offices from %s: %s', excel_path, exc)
