from django.core.management.base import BaseCommand, CommandError
import os
import json
import pandas as pd


class Command(BaseCommand):
    help = 'Import tax offices from an Excel file and write JSON used by onboarding.'

    def add_arguments(self, parser):
        parser.add_argument('input', nargs='?', help='Path to Excel file (xlsx). Default: ./tax_org.xlsx', default=None)
        parser.add_argument('--output', help='Output JSON path. Default: backend/organization/data/tax_offices.json', default=None)

    def handle(self, *args, **options):
        input_path = options.get('input')
        if not input_path:
            input_path = os.path.join(os.getcwd(), 'tax_org.xlsx')

        # determine default output inside the organization app
        if options.get('output'):
            output_path = options.get('output')
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(app_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            output_path = os.path.join(data_dir, 'tax_offices.json')

        if not os.path.exists(input_path):
            raise CommandError(f'Input file not found: {input_path}')

        try:
            df = pd.read_excel(input_path, header=None, engine='openpyxl', dtype=str)
        except Exception as exc:
            raise CommandError(f'Failed to read Excel file: {exc}')

        header_candidates = {
            'код', 'наименование', 'code', 'name', 'tax_office_code', 'tax_office_name',
            'tax office code', 'tax office name', 'tax_office', 'tax office'
        }

        offices = []
        for _, row in df.iterrows():
            # get first two columns if present
            code = ''
            name = ''
            try:
                code = str(row[0]).strip() if not pd.isna(row[0]) else ''
            except Exception:
                code = ''
            try:
                name = str(row[1]).strip() if len(row) > 1 and not pd.isna(row[1]) else ''
            except Exception:
                name = ''

            if not code and not name:
                continue

            if code.lower() in header_candidates or name.lower() in header_candidates:
                continue

            offices.append({'code': code, 'name': name})

        # deduplicate by code (keep first occurrence)
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

        try:
            with open(output_path, 'w', encoding='utf-8') as fh:
                json.dump(deduped, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            raise CommandError(f'Failed to write JSON: {exc}')

        self.stdout.write(self.style.SUCCESS(f'Wrote {len(deduped)} tax offices to {output_path}'))
