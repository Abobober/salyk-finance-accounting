from __future__ import annotations

from io import BytesIO
from pathlib import Path
from decimal import Decimal, InvalidOperation

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:
    from pypdf import PdfReader, PdfWriter
except Exception:  # pragma: no cover
    PdfReader = None
    PdfWriter = None


FONT_NAME = 'Helvetica'
CYRILLIC_FONT_NAME = 'Helvetica'
for candidate in (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    'C:/Windows/Fonts/arial.ttf',
    'C:/Windows/Fonts/Arial.ttf',
    'C:/Windows/Fonts/tahoma.ttf',
):
    if Path(candidate).exists():
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', candidate))
            FONT_NAME = 'DejaVuSans'
            CYRILLIC_FONT_NAME = 'DejaVuSans'
            break
        except Exception:
            pass


PAGE1_FIELD_POSITIONS = {
    '102': ('left', 52, 83, 10),
    '103': ('left', 305, 83, 10),
    '104': ('left', 52, 114, 9),
    '104_name': ('left', 112, 114, 9),
    '105': ('left', 442, 114, 9),
    '201': ('center', 183, 143, 9),
    '202': ('center', 353, 143, 9),
}

CHECKBOX_POSITIONS = {
    '001_initial': (144, 53),
    '001_amended': (223, 53),
    '001_liquidation': (325, 53),
}

HEADER_SPLIT_LAYOUTS = {
    # 14 digits of TIN, rendered one digit at a time with tighter spacing.
    '102': {'start_x': 71, 'top': 83, 'font_size': 11, 'max_len': 14, 'gap_spaces': 2.6},
    # Tax office code (usually 3 digits) is rendered into split cells.
    '104': {'start_x': 56, 'top': 114, 'font_size': 9, 'max_len': 3, 'gap_spaces': 3.2},
    # 8 digits of date (ddmmyyyy), rendered one digit at a time with tighter spacing.
        '201': {'start_x': 260, 'top': 143, 'font_size': 9, 'max_len': 8, 'gap_spaces': 4.2},
    '202': {'start_x': 430, 'top': 143, 'font_size': 9, 'max_len': 8, 'gap_spaces': 4.2},
}

# Alignment presets for different STI-091 template revisions/scans.
# Switch ACTIVE_ALIGNMENT_PRESET to quickly calibrate rendering.
ALIGNMENT_PRESETS = {
    'tight': {
        'global_x': Decimal('-3.0'),
        'global_y': Decimal('1.0'),
        'checkbox_x': Decimal('-1.5'),
        'checkbox_y': Decimal('0.5'),
        'header_x': Decimal('0.0'),
        'header_y': Decimal('0.0'),
        'organization_x': Decimal('0.0'),
        'organization_y': Decimal('0.0'),
        'tax_office_x': Decimal('0.0'),
        'tax_office_y': Decimal('0.0'),
        'contact_phone_x': Decimal('0.0'),
        'contact_phone_y': Decimal('0.0'),
        'inn_x': Decimal('0.0'),
        'inn_y': Decimal('0.0'),
        'date_x': Decimal('0.0'),
        'date_y': Decimal('0.0'),
        'numeric_x': Decimal('0.5'),
        'numeric_y': Decimal('-0.8'),
        'columns': {'base': 418, 'rate': 499, 'tax': 577},
    },
    'normal': {
        'global_x': Decimal('-2.0'),
        'global_y': Decimal('2.0'),
        'checkbox_x': Decimal('5.0'),
        'checkbox_y': Decimal('-7.0'),
        'header_x': Decimal('10.0'),
        'header_y': Decimal('-23.0'),
        'organization_x': Decimal('0.0'),
        'organization_y': Decimal('-24.0'),
        'tax_office_x': Decimal('-17.0'),
        'tax_office_y': Decimal('-18.0'),
        'contact_phone_x': Decimal('4.0'),
        'contact_phone_y': Decimal('-20.0'),
        'inn_x': Decimal('-9.0'),
        'inn_y': Decimal('-23.0'),
        'date_x': Decimal('-73.0'),
        'date_y': Decimal('-9.0'),
        'numeric_x': Decimal('-10.5'),
        'numeric_y': Decimal('-8.0'),
        'columns': {'base': 420, 'rate': 501, 'tax': 579},
    },
    'legacy': {
        'global_x': Decimal('0.0'),
        'global_y': Decimal('0.0'),
        'checkbox_x': Decimal('0.0'),
        'checkbox_y': Decimal('0.0'),
        'header_x': Decimal('0.0'),
        'header_y': Decimal('0.0'),
        'organization_x': Decimal('0.0'),
        'organization_y': Decimal('0.0'),
        'tax_office_x': Decimal('0.0'),
        'tax_office_y': Decimal('0.0'),
        'contact_phone_x': Decimal('0.0'),
        'contact_phone_y': Decimal('0.0'),
        'inn_x': Decimal('0.0'),
        'inn_y': Decimal('0.0'),
        'date_x': Decimal('0.0'),
        'date_y': Decimal('0.0'),
        'numeric_x': Decimal('0.0'),
        'numeric_y': Decimal('0.0'),
        'columns': {'base': 425, 'rate': 506, 'tax': 584},
    },
}
ACTIVE_ALIGNMENT_PRESET = 'normal'

NUMERIC_LABEL_TOPS = {
    '050': 206.22, '051': 206.22, '052': 206.22,
    '053': 234.28, '054': 233.83, '055': 233.87,
    '056': 248.15, '057': 248.15, '058': 248.42,
    '059': 263.28,
    '060': 283.45, '061': 283.2, '062': 283.2,
    '063': 297.58, '064': 297.62, '065': 297.28,
    '066': 311.25,
    '067': 329.65, '068': 329.58, '069': 329.53,
    '070': 342.27, '071': 342.03, '072': 342.15,
    '073': 355.4,
    '074': 375.02, '075': 375.0, '076': 375.0,
    '077': 387.7, '078': 387.7, '079': 387.7,
    '080': 400.06,
    '130': 426.48, '131': 426.6, '132': 426.53,
    '133': 442.33, '134': 442.33, '135': 442.32,
    '136': 458.15, '137': 458.1, '138': 458.1,
    '139': 470.15, '140': 470.15, '141': 470.15,
    '142': 482.28, '143': 482.28, '144': 482.28,
    '145': 494.68, '146': 494.68, '147': 494.68,
    '148': 513.67, '149': 513.25, '150': 513.25,
    '151': 531.9, '152': 531.8, '153': 531.87,
    '154': 552.72, '155': 552.72, '156': 552.72,
    '157': 570.95, '158': 570.76, '159': 570.7,
    '160': 591.98, '161': 591.6, '162': 592.08,
    '163': 612.65, '164': 612.23, '165': 612.28,
    '166': 625.6, '167': 625.6, '168': 625.83,
    '169': 639.65,
    '170': 655.3, '171': 655.7, '172': 655.3,
    '173': 675.48, '174': 675.53, '175': 675.53,
    '176': 695.6, '177': 695.55, '178': 696.3,
    '179': 715.88, '180': 715.87, '181': 715.87,
    '182': 735.78, '183': 735.57,
    '184': 754.03, '185': 753.78,
    '186': 780.67, '187': 780.58,
}

COLUMN_RIGHT_EDGE = ALIGNMENT_PRESETS[ACTIVE_ALIGNMENT_PRESET]['columns']

CELL_COLUMN_BY_ID = {
    **{cell: 'base' for cell in ['050', '053', '056', '060', '063', '067', '070', '074', '077', '130', '133', '136', '139', '142', '145', '148', '151', '154', '157', '160', '163', '166', '170', '173', '176', '179', '182', '184', '186']},
    **{cell: 'rate' for cell in ['051', '054', '057', '061', '064', '068', '071', '075', '078', '131', '134', '137', '140', '143', '146', '149', '152', '155', '158', '161', '164', '167', '171', '174', '177', '180']},
    **{cell: 'tax' for cell in ['052', '055', '058', '059', '062', '065', '066', '069', '072', '073', '076', '079', '080', '132', '135', '138', '141', '144', '147', '150', '153', '156', '159', '162', '165', '168', '169', '172', '175', '178', '181', '183', '185', '187']},
}


def resolve_point(base_x: float, base_y: float, preset: dict, field_kind: str = 'text') -> tuple[float, float]:
    x = Decimal(str(base_x)) + preset['global_x']
    y = Decimal(str(base_y)) + preset['global_y']

    if field_kind == 'checkbox':
        x += preset['checkbox_x']
        y += preset['checkbox_y']
    elif field_kind == 'header':
        x += preset.get('header_x', Decimal('0.0'))
        y += preset.get('header_y', Decimal('0.0'))
    elif field_kind == 'organization':
        x += preset.get('organization_x', Decimal('0.0'))
        y += preset.get('organization_y', Decimal('0.0'))
    elif field_kind == 'tax_office':
        x += preset.get('tax_office_x', Decimal('0.0'))
        y += preset.get('tax_office_y', Decimal('0.0'))
    elif field_kind == 'contact_phone':
        x += preset.get('contact_phone_x', Decimal('0.0'))
        y += preset.get('contact_phone_y', Decimal('0.0'))
    elif field_kind == 'inn':
        x += preset.get('inn_x', Decimal('0.0'))
        y += preset.get('inn_y', Decimal('0.0'))
    elif field_kind == 'date':
        x += preset.get('date_x', Decimal('0.0'))
        y += preset.get('date_y', Decimal('0.0'))
    elif field_kind == 'numeric':
        x += preset['numeric_x']
        y += preset['numeric_y']

    return float(x), float(y)


class UnifiedTaxPDFGenerator:
    @staticmethod
    def _preset():
        return ALIGNMENT_PRESETS.get(ACTIVE_ALIGNMENT_PRESET, ALIGNMENT_PRESETS['normal'])

    def __init__(self, report_data, template_path):
        self.report_data = report_data
        self.template_path = Path(template_path)

    @staticmethod
    def _is_truthy(value) -> bool:
        return str(value).strip().lower() in {'1', 'true', 'x', 'yes'}

    @staticmethod
    def _format_kg_number(text: str) -> str:
        normalized = text.replace(' ', '')
        try:
            number = Decimal(normalized)
        except (InvalidOperation, ValueError):
            return text
        rendered = f'{number:,.2f}'.replace(',', ' ').replace('.', ',')
        return rendered

    @classmethod
    def _display_value(cls, value, *, keep_zeros: bool = False, numeric: bool = False) -> str:
        text = '' if value is None else str(value)
        if text in {'', 'None'}:
            return ''
        if not keep_zeros and text in {'0.00', '0', '0.0'}:
            return ''
        if numeric:
            return cls._format_kg_number(text)
        return text

    @staticmethod
    def _digits_only(value: object) -> str:
        return ''.join(ch for ch in str(value or '') if ch.isdigit())

    @classmethod
    def _tax_office_name(cls, header: dict) -> str:
        name = cls._display_value(header.get('104_name'), keep_zeros=True)
        if name:
            return name

        full_value = cls._display_value(header.get('104'), keep_zeros=True)
        digits = cls._digits_only(full_value)
        if not full_value or not digits:
            return full_value

        trimmed = full_value
        if trimmed.startswith(digits):
            trimmed = trimmed[len(digits):]
        return trimmed.lstrip(' -/.,')

    def _draw_split_digits(
        self,
        pdf,
        *,
        raw_value: object,
        layout: dict[str, float],
        height: float,
        preset: dict,
        field_kind: str,
    ) -> bool:
        digits = self._digits_only(raw_value)
        if not digits:
            return False

        top = layout['top']
        start_x = layout['start_x']
        # Supports fractional spacing (e.g. 1.35, 1.8) for fine calibration.
        try:
            gap_spaces = float(layout.get('gap_spaces', 1))
        except (TypeError, ValueError):
            gap_spaces = 1.0
        max_len = int(layout['max_len'])
        font_size = layout['font_size']
        y = height - top

        space_width = pdf.stringWidth(' ', FONT_NAME, font_size)
        digit_step = (
            pdf.stringWidth('0', FONT_NAME, font_size)
            + (space_width * gap_spaces)
        )

        pdf.setFont(FONT_NAME, font_size)
        for index, digit in enumerate(digits[:max_len]):
            x = start_x + (index * digit_step)
            draw_x, draw_y = resolve_point(x, y, preset, field_kind=field_kind)
            pdf.drawString(draw_x, draw_y, digit)
        return True

    def _page1_overlay(self, width: float, height: float):
        packet = BytesIO()
        pdf = canvas.Canvas(packet, pagesize=(width, height))
        pdf.setFont(FONT_NAME, 10)
        preset = self._preset()

        cells = self.report_data['cells']
        header = self.report_data.get('header') or {}
        period = self.report_data.get('period') or {}
        synthetic_cells = {
            **cells,
            '102': header.get('102', ''),
            '103': header.get('103', ''),
            '104': header.get('104_code') or header.get('104', ''),
            '104_name': self._tax_office_name(header),
            '105': header.get('105') or header.get('115', ''),
            '201': cells.get('201') or period.get('start', ''),
            '202': cells.get('202') or period.get('end', ''),
        }

        # TIN and period dates are printed digit-by-digit into separate boxes.
        split_rendered = set()
        if self._draw_split_digits(
            pdf,
            raw_value=synthetic_cells.get('102'),
            layout=HEADER_SPLIT_LAYOUTS['102'],
            height=height,
            preset=preset,
            field_kind='inn',
        ):
            split_rendered.add('102')
        if self._draw_split_digits(
            pdf,
            raw_value=synthetic_cells.get('104'),
            layout=HEADER_SPLIT_LAYOUTS['104'],
            height=height,
            preset=preset,
            field_kind='tax_office',
        ):
            split_rendered.add('104')
        if self._draw_split_digits(
            pdf,
            raw_value=synthetic_cells.get('201'),
            layout=HEADER_SPLIT_LAYOUTS['201'],
            height=height,
            preset=preset,
            field_kind='date',
        ):
            split_rendered.add('201')
        if self._draw_split_digits(
            pdf,
            raw_value=synthetic_cells.get('202'),
            layout=HEADER_SPLIT_LAYOUTS['202'],
            height=height,
            preset=preset,
            field_kind='date',
        ):
            split_rendered.add('202')

        for key, (mode, x, top, font_size) in PAGE1_FIELD_POSITIONS.items():
            if key in split_rendered:
                continue
            value = self._display_value(synthetic_cells.get(key), keep_zeros=True)
            if not value:
                continue
            pdf.setFont(FONT_NAME, font_size)
            y = height - top
            if key == '103':
                field_kind = 'organization'
            elif key in {'104', '104_name'}:
                field_kind = 'tax_office'
            elif key == '105':
                field_kind = 'contact_phone'
            else:
                field_kind = 'text'
            x, y = resolve_point(x, y, preset, field_kind=field_kind)
            if mode == 'left':
                pdf.drawString(x, y, value)
            else:
                pdf.drawCentredString(x, y, value)

        pdf.setFont(FONT_NAME, 12)
        for key, (x, top) in CHECKBOX_POSITIONS.items():
            if self._is_truthy(synthetic_cells.get(key)):
                x, y = resolve_point(x, height - top, preset, field_kind='checkbox')
                pdf.drawString(x, y, 'X')

        pdf.setFont(FONT_NAME, 8.5)
        for cell_id, top in NUMERIC_LABEL_TOPS.items():
            value = self._display_value(synthetic_cells.get(cell_id), keep_zeros=True, numeric=True)
            if not value:
                continue
            column = CELL_COLUMN_BY_ID[cell_id]
            x = COLUMN_RIGHT_EDGE[column]
            y = height - top
            x, y = resolve_point(x, y, preset, field_kind='numeric')
            pdf.drawRightString(x, y, value)

        pdf.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def _appendix_pdf(self):
        packet = BytesIO()
        pdf = canvas.Canvas(packet, pagesize=A4)
        width, height = A4

        def header(title: str, y: float):
            pdf.setFont(CYRILLIC_FONT_NAME, 14)
            pdf.drawString(40, y, title)
            return y - 22

        def text(line: str, y: float, size: int = 9):
            pdf.setFont(CYRILLIC_FONT_NAME, size)
            pdf.drawString(40, y, line)
            return y - (size + 4)

        report_period = self.report_data.get('period') or {}
        report_header = self.report_data.get('header') or {}
        advance_tables = self.report_data.get('advance_tables') or {}
        current_rows = advance_tables.get('current_period_advance_payments') or []
        previous_rows = advance_tables.get('previous_period_advance_offsets') or []

        y = height - 40
        y = header('Приложение STI-091_9-001', y)
        y = text(f"Период: {report_period.get('start', '-')} - {report_period.get('end', '-')}", y)
        y = text(f"Налогоплательщик: {report_header.get('103') or '-'}", y)
        y = text(f"ИНН: {report_header.get('102') or '-'}", y)
        y -= 10

        def render_table(title: str, rows: list[dict], y_value: float):
            y_value = header(title, y_value)
            if not rows:
                return text('Нет строк.', y_value)

            pdf.setFont(CYRILLIC_FONT_NAME, 9)
            pdf.drawString(40, y_value, 'Описание')
            pdf.drawString(280, y_value, 'Сумма')
            pdf.drawString(380, y_value, 'Ставка %')
            pdf.drawString(470, y_value, 'Налог')
            y_value -= 14
            for row in rows:
                if y_value < 70:
                    pdf.showPage()
                    y_value = height - 40
                    y_value = header('Приложение STI-091_9-001 (продолжение)', y_value)
                pdf.setFont(CYRILLIC_FONT_NAME, 8)
                pdf.drawString(40, y_value, row['description'][:45])
                pdf.drawRightString(340, y_value, row['amount'])
                pdf.drawRightString(430, y_value, row['rate'])
                pdf.drawRightString(540, y_value, row['tax'])
                y_value -= 13
            return y_value - 10

        if current_rows or previous_rows:
            y = render_table('Текущие авансовые платежи', current_rows, y)
            y = render_table('Зачеты авансов прошлых периодов', previous_rows, y)

        y -= 6
        y = header('Проверка и замечания', y)
        issues = self.report_data.get('issues') or []
        if not issues:
            y = text('Блокирующих ошибок и предупреждений нет.', y)
        else:
            for issue in issues:
                if y < 80:
                    pdf.showPage()
                    y = height - 40
                    y = header('Приложение STI-091_9-001 (продолжение)', y)
                line = f"[{issue['severity'].upper()}] {issue['message']}"
                y = text(line[:110], y, size=8)

        pdf.save()
        packet.seek(0)
        return PdfReader(packet)

    def generate(self, output_path):
        if PdfReader is None or PdfWriter is None:
            raise RuntimeError('pypdf is required to generate STI-091 PDF.')

        template_reader = PdfReader(str(self.template_path))
        writer = PdfWriter()

        first_page = template_reader.pages[0]
        overlay = self._page1_overlay(float(first_page.mediabox.width), float(first_page.mediabox.height))
        first_page.merge_page(overlay)
        writer.add_page(first_page)

        advance_tables = self.report_data.get('advance_tables') or {}
        if advance_tables.get('current_period_advance_payments') or advance_tables.get('previous_period_advance_offsets'):
            appendix_reader = self._appendix_pdf()
            for page in appendix_reader.pages:
                writer.add_page(page)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('wb') as fh:
            writer.write(fh)
