from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from finance.models import Transaction
from organization.models import OrganizationActivity


ZERO = Decimal('0.00')
TWO_PLACES = Decimal('0.01')
HEADER_PLACEHOLDER = '000'
TIN_PLACEHOLDER = '00000000000000'
PHONE_PLACEHOLDER = '+996555555555'


LINE_CONFIG = {
    'trade_preferential': {
        'mode': 'single',
        'base_cell': '050',
        'rate_cell': '051',
        'tax_cell': '052',
        'label': 'Торговая деятельность - льготная строка до 50 млн',
    },
    'trade_general': {
        'mode': 'split',
        'cash': ('053', '054', '055'),
        'non_cash': ('056', '057', '058'),
        'total_cell': '059',
        'label': 'Торговая деятельность',
    },
    'production': {
        'mode': 'split',
        'cash': ('060', '061', '062'),
        'non_cash': ('063', '064', '065'),
        'total_cell': '066',
        'label': 'Производство/переработка/ПО/туризм',
    },
    'other': {
        'mode': 'split',
        'cash': ('067', '068', '069'),
        'non_cash': ('070', '071', '072'),
        'total_cell': '073',
        'label': 'Прочие виды деятельности',
    },
    'public_catering': {
        'mode': 'split',
        'cash': ('074', '075', '076'),
        'non_cash': ('077', '078', '079'),
        'total_cell': '080',
        'label': 'Общественное питание',
    },
    'garment_textile': {'mode': 'single', 'base_cell': '130', 'rate_cell': '131', 'tax_cell': '132', 'label': 'Швейное и/или текстильное производство'},
    'jewelry': {'mode': 'single', 'base_cell': '133', 'rate_cell': '134', 'tax_cell': '135', 'label': 'Ювелирные изделия'},
    'lottery': {'mode': 'single', 'base_cell': '136', 'rate_cell': '137', 'tax_cell': '138', 'label': 'Лотерейная деятельность'},
    'sauna': {'mode': 'single', 'base_cell': '139', 'rate_cell': '140', 'tax_cell': '141', 'label': 'Сауна'},
    'billiard': {'mode': 'single', 'base_cell': '142', 'rate_cell': '143', 'tax_cell': '144', 'label': 'Бильярд'},
    'banya': {'mode': 'single', 'base_cell': '145', 'rate_cell': '146', 'tax_cell': '147', 'label': 'Баня'},
    'creative_park': {'mode': 'single', 'base_cell': '148', 'rate_cell': '149', 'tax_cell': '150', 'label': 'Резидент парка креативной индустрии'},
    'article_324_export': {'mode': 'single', 'base_cell': '151', 'rate_cell': '152', 'tax_cell': '153', 'label': 'Режим статьи 324 НК КР'},
    'agri_procurement': {'mode': 'single', 'base_cell': '154', 'rate_cell': '155', 'tax_cell': '156', 'label': 'Сельхоззаготовитель'},
    'milk_procurement': {'mode': 'single', 'base_cell': '157', 'rate_cell': '158', 'tax_cell': '159', 'label': 'Сельхоззаготовитель молока'},
    'anonymous_subject_423': {'mode': 'single', 'base_cell': '160', 'rate_cell': '161', 'tax_cell': '162', 'label': 'Реализация товаров обезличенному субъекту'},
    'fez_partial': {'mode': 'single', 'base_cell': '163', 'rate_cell': '164', 'tax_cell': '165', 'label': 'СЭЗ с частичной переработкой'},
    'fez_unchanged': {'mode': 'single', 'base_cell': '166', 'rate_cell': '167', 'tax_cell': '168', 'label': 'СЭЗ в неизмененном виде'},
    'school_catering_ip': {'mode': 'single', 'base_cell': '170', 'rate_cell': '171', 'tax_cell': '172', 'label': 'Питание учащихся школ КР'},
    'state_real_estate_exchange': {'mode': 'single', 'base_cell': '173', 'rate_cell': '174', 'tax_cell': '175', 'label': 'Недвижимость для госнужд'},
    'virtual_asset': {'mode': 'single', 'base_cell': '176', 'rate_cell': '177', 'tax_cell': '178', 'label': 'Реализация виртуального актива'},
    'outside_kr': {'mode': 'single', 'base_cell': '179', 'rate_cell': '180', 'tax_cell': '181', 'label': 'Деятельность вне территории КР'},
}


DEFAULT_RATE_BY_CELL = {
    '051': Decimal('0.50'),
    '054': Decimal('4.00'),
    '057': Decimal('2.00'),
    '061': Decimal('4.00'),
    '064': Decimal('2.00'),
    '068': Decimal('6.00'),
    '071': Decimal('4.00'),
    '075': Decimal('6.00'),
    '078': Decimal('4.00'),
    '131': Decimal('0.25'),
    '134': Decimal('0.25'),
    '137': Decimal('0.00'),
    '140': Decimal('8.00'),
    '143': Decimal('8.00'),
    '146': Decimal('8.00'),
    '149': Decimal('1.00'),
    '152': Decimal('3.00'),
    '155': Decimal('0.50'),
    '158': Decimal('0.25'),
    '161': Decimal('4.00'),
    '164': Decimal('1.00'),
    '167': Decimal('3.00'),
    '171': Decimal('1.00'),
    '174': Decimal('0.00'),
    '177': Decimal('8.00'),
    '180': Decimal('0.00'),
}


ADVANCE_CURRENT_TOTAL_AMOUNT_CELL = '182'
ADVANCE_CURRENT_TOTAL_TAX_CELL = '183'
ADVANCE_PREVIOUS_TOTAL_AMOUNT_CELL = '184'
ADVANCE_PREVIOUS_TOTAL_TAX_CELL = '185'
TOTAL_BASE_CELL = '186'
TOTAL_TAX_CELL = '187'

BASE_TOTAL_CELLS = [
    '050', '053', '056', '060', '063', '067', '070', '074', '077', '130', '133', '136', '139',
    '142', '145', '148', '151', '154', '157', '160', '163', '166', '170', '173', '176', '179',
]
TAX_TOTAL_CELLS = [
    '052', '059', '066', '073', '080', '132', '135', '138', '141', '144', '147', '150', '153',
    '156', '159', '162', '165', '169', '172', '175', '178', '181',
]

ALL_FORM_CELLS = [
    '050', '051', '052', '053', '054', '055', '056', '057', '058', '059',
    '060', '061', '062', '063', '064', '065', '066', '067', '068', '069',
    '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
    '080', '130', '131', '132', '133', '134', '135', '136', '137', '138',
    '139', '140', '141', '142', '143', '144', '145', '146', '147', '148',
    '149', '150', '151', '152', '153', '154', '155', '156', '157', '158',
    '159', '160', '161', '162', '163', '164', '165', '166', '167', '168',
    '169', '170', '171', '172', '173', '174', '175', '176', '177', '178',
    '179', '180', '181', '182', '183', '184', '185', '186', '187',
]


def _first_non_blank(*values) -> str:
    for value in values:
        text = (value or '').strip()
        if text:
            return text
    return ''


def _join_non_blank(*values) -> str:
    return ' '.join((value or '').strip() for value in values if (value or '').strip())


def _full_name(user) -> str:
    return _join_non_blank(getattr(user, 'first_name', ''), getattr(user, 'last_name', ''))


def _activity_code_prefix(activity) -> str:
    return str(getattr(activity, 'code', '') or '').strip().split('.')[0]


@dataclass
class Bucket:
    base: Decimal = ZERO
    tax: Decimal = ZERO
    rates: set[Decimal] = field(default_factory=set)
    transaction_count: int = 0


class STI091ReportDataBuilder:
    def __init__(
        self,
        organization,
        year: int,
        quarter: int,
        *,
        report_kind: str = 'initial',
        tin: str = '',
        taxpayer_name: str = '',
        tax_office: str = '',
        contact_phone: str = '',
        activity_line_map: dict[str, str] | None = None,
        current_period_advance_payments: list[dict] | None = None,
        previous_period_advance_offsets: list[dict] | None = None,
    ):
        self.organization = organization
        self.user = organization.user
        self.year = year
        self.quarter = int(quarter)
        self.report_kind = report_kind
        self.activity_line_map = activity_line_map or {}
        self.current_period_advance_payments = current_period_advance_payments or []
        self.previous_period_advance_offsets = previous_period_advance_offsets or []
        self.tax_office_code = _first_non_blank(
            getattr(self.organization, 'tax_authority_code', ''),
            getattr(self.organization, 'tax_office_code', ''),
        )
        self.tax_office_name = _first_non_blank(
            getattr(self.organization, 'tax_authority_name', ''),
            getattr(self.organization, 'tax_office_name', ''),
        )
        organization_tax_office = _join_non_blank(self.tax_office_code, self.tax_office_name)
        user_full_name = _full_name(self.user)
        taxpayer_name_fallback = user_full_name if self.organization.org_type == self.organization.OrgType.IE else ''
        self.tin = _first_non_blank(tin, getattr(self.organization, 'inn', ''), getattr(self.organization, 'tin', ''))
        self.taxpayer_name = _first_non_blank(
            taxpayer_name,
            getattr(self.organization, 'taxpayer_name', ''),
            taxpayer_name_fallback,
        )
        self.tax_office = _first_non_blank(tax_office, organization_tax_office)
        self.contact_phone = _first_non_blank(
            contact_phone,
            getattr(self.organization, 'contact_phone', ''),
            getattr(self.user, 'phone', ''),
        )
        self.issues: list[dict[str, object]] = []
    def get_period_dates(self):
        if self.quarter == 1:
            return date(self.year, 1, 1), date(self.year, 3, 31)
        if self.quarter == 2:
            return date(self.year, 4, 1), date(self.year, 6, 30)
        if self.quarter == 3:
            return date(self.year, 7, 1), date(self.year, 9, 30)
        return date(self.year, 10, 1), date(self.year, 12, 31)

    def get_transactions(self):
        start, end = self.get_period_dates()
        return list(
            Transaction.objects.filter(
                user=self.user,
                transaction_type=Transaction.TransactionType.INCOME,
                is_taxable=True,
                transaction_date__range=(start, end),
            ).select_related('activity_code').order_by('transaction_date', 'id')
        )

    def get_org_activities(self):
        activities = list(
            OrganizationActivity.objects.filter(profile=self.organization)
            .select_related('activity')
            .order_by('-is_primary', 'activity__code')
        )
        return activities, {item.activity_id: item for item in activities}

    def _add_issue(self, code: str, severity: str, message: str, **details):
        payload = {'code': code, 'severity': severity, 'message': message}
        if details:
            payload['details'] = details
        self.issues.append(payload)

    def _quantize(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    def _money(self, value: Decimal) -> str:
        return f'{self._quantize(value):.2f}'

    def _rate(self, value: Decimal) -> str:
        return f'{self._quantize(value):.2f}'

    def _default_rate(self, rate_cell: str) -> Decimal:
        return DEFAULT_RATE_BY_CELL.get(rate_cell, ZERO)

    def _resolve_transaction_rate(
        self,
        transaction,
        org_activity_map: dict[int, OrganizationActivity],
        default_rate: Decimal,
        fallback_org_activity: OrganizationActivity | None = None,
    ):
        snapshot_rate = (
            transaction.cash_tax_rate
            if transaction.payment_method == Transaction.PaymentMethod.CASH
            else transaction.non_cash_tax_rate
        )
        if snapshot_rate is not None:
            return Decimal(snapshot_rate), 'transaction_snapshot'

        org_activity = org_activity_map.get(transaction.activity_code_id) or fallback_org_activity
        if org_activity is None:
            return default_rate, 'form_default'

        fallback_rate = (
            org_activity.cash_tax_rate
            if transaction.payment_method == Transaction.PaymentMethod.CASH
            else org_activity.non_cash_tax_rate
        )
        if fallback_rate is None:
            return default_rate, 'form_default'
        return Decimal(fallback_rate), 'organization_activity'

    def _resolve_line_for_activity(self, activity, fallback_activity=None):
        if activity is None:
            if fallback_activity is not None:
                self._add_issue(
                    'missing_activity_code_used_primary',
                    'warning',
                    'У транзакции отсутствует activity_code, применен основной вид деятельности профиля.',
                )
                activity = fallback_activity
            else:
                self._add_issue(
                    'missing_activity_code',
                    'warning',
                    'У транзакции отсутствует activity_code, сумма включена в строку "Прочие виды деятельности".',
                )
                return 'other'

        candidates = [str(activity.id), getattr(activity, 'code', None)]
        for candidate in candidates:
            if candidate and candidate in self.activity_line_map:
                return self.activity_line_map[candidate]

        if _activity_code_prefix(activity) == '56':
            return 'public_catering'

        return 'other'

    def _advance_rows(self, rows: list[dict]):
        normalized = []
        total_amount = ZERO
        total_tax = ZERO
        for index, row in enumerate(rows, start=1):
            amount = self._quantize(Decimal(row['amount']))
            rate = self._quantize(Decimal(row['rate']))
            tax = self._quantize(amount * rate / Decimal('100'))
            normalized.append({
                'description': (row.get('description') or f'Аванс {index}').strip(),
                'amount': self._money(amount),
                'rate': self._rate(rate),
                'tax': self._money(tax),
            })
            total_amount += amount
            total_tax += tax
        return normalized, self._quantize(total_amount), self._quantize(total_tax)

    def _initial_cells(self, date_from: date, date_to: date):
        tin_value = self.tin or TIN_PLACEHOLDER
        taxpayer_name_value = self.taxpayer_name or HEADER_PLACEHOLDER
        tax_office_value = self.tax_office or HEADER_PLACEHOLDER
        contact_phone_value = self.contact_phone or PHONE_PLACEHOLDER

        cells = {cell: '0.00' for cell in ALL_FORM_CELLS}
        cells.update({
            '001_initial': self.report_kind == 'initial',
            '001_amended': self.report_kind == 'amended',
            '001_liquidation': self.report_kind == 'liquidation',
            '102': tin_value,
            '103': taxpayer_name_value,
            '104': tax_office_value,
            '104_code': self.tax_office_code,
            '104_name': self.tax_office_name,
            '105': contact_phone_value,
            '115': contact_phone_value,
            '201': date_from.strftime('%d.%m.%Y'),
            '202': date_to.strftime('%d.%m.%Y'),
        })
        return cells

    def _compute_formula_tax(self, cells, base_cell, rate_cell, tax_cell, *, bucket: Bucket | None = None):
        rate_text = cells.get(rate_cell, '')
        if rate_text:
            tax_value = self._quantize(Decimal(cells[base_cell]) * Decimal(rate_text) / Decimal('100'))
            cells[tax_cell] = self._money(tax_value)
            return tax_value
        if bucket is not None:
            cells[tax_cell] = self._money(bucket.tax)
            return bucket.tax
        cells[tax_cell] = '0.00'
        return ZERO

    def build_report_data(self):
        date_from, date_to = self.get_period_dates()
        transactions = self.get_transactions()
        org_activities, org_activity_map = self.get_org_activities()
        primary_org_activity = next((item for item in org_activities if item.is_primary), None)

        cells: dict[str, object] = self._initial_cells(date_from, date_to)
        buckets: dict[str, Bucket | dict[str, Bucket]] = {}
        for line_key, config in LINE_CONFIG.items():
            if config['mode'] == 'split':
                buckets[line_key] = {
                    'cash': Bucket(),
                    'non_cash': Bucket(),
                }
            else:
                buckets[line_key] = Bucket()

        if self.organization.tax_regime != self.organization.TaxRegime.SINGLE:
            self._add_issue(
                'wrong_tax_regime',
                'error',
                'Профиль организации не находится на режиме единого налога.',
                tax_regime=self.organization.tax_regime,
            )
        if not self.tin:
            self._add_issue('missing_tin', 'error', 'Не заполнен ИНН налогоплательщика.')
        if not self.taxpayer_name:
            self._add_issue('missing_taxpayer_name', 'error', 'Не заполнено ФИО/наименование налогоплательщика.')
        if not self.tax_office:
            self._add_issue('missing_tax_office', 'warning', 'Не заполнен код и наименование налогового органа.')
        if not self.contact_phone:
            self._add_issue('missing_contact_phone', 'warning', 'Не заполнен контактный телефон.')

        for tx in transactions:
            amount = self._quantize(tx.amount or ZERO)
            if not tx.is_business:
                self._add_issue(
                    'non_business_taxable_income_included',
                    'warning',
                    'Облагаемый доход без признака бизнес-операции включен в STI-091.',
                    transaction_id=tx.id,
                )
            fallback_org_activity = primary_org_activity if tx.activity_code_id is None else None
            fallback_activity = fallback_org_activity.activity if fallback_org_activity else None
            line_key = self._resolve_line_for_activity(tx.activity_code, fallback_activity)

            config = LINE_CONFIG[line_key]
            if config['mode'] == 'split':
                bucket = buckets[line_key][tx.payment_method]
                _base_cell, rate_cell, _tax_cell = config[tx.payment_method]
            else:
                bucket = buckets[line_key]
                rate_cell = config['rate_cell']

            rate, rate_source = self._resolve_transaction_rate(
                tx,
                org_activity_map,
                self._default_rate(rate_cell),
                fallback_org_activity,
            )

            bucket.base += amount
            bucket.transaction_count += 1

            bucket.rates.add(self._quantize(rate))
            bucket.tax += self._quantize(amount * rate / Decimal('100'))

        for line_key, config in LINE_CONFIG.items():
            if config['mode'] == 'split':
                total_tax = ZERO
                for payment_method in ('cash', 'non_cash'):
                    bucket = buckets[line_key][payment_method]
                    base_cell, rate_cell, tax_cell = config[payment_method]
                    cells[base_cell] = self._money(bucket.base)
                    if len(bucket.rates) == 1:
                        cells[rate_cell] = self._rate(next(iter(bucket.rates)))
                    elif len(bucket.rates) > 1:
                        cells[rate_cell] = self._rate(self._default_rate(rate_cell))
                        self._add_issue(
                            'multiple_rates_for_cell',
                            'warning',
                            'В одной строке формы обнаружено несколько ставок, применена ставка формы.',
                            line_key=line_key,
                            payment_method=payment_method,
                            cell=rate_cell,
                            rates=[self._rate(rate) for rate in sorted(bucket.rates)],
                        )
                    else:
                        cells[rate_cell] = self._rate(self._default_rate(rate_cell))
                    total_tax += self._compute_formula_tax(cells, base_cell, rate_cell, tax_cell, bucket=bucket)
                cells[config['total_cell']] = self._money(total_tax)
            else:
                bucket = buckets[line_key]
                cells[config['base_cell']] = self._money(bucket.base)
                if len(bucket.rates) == 1:
                    cells[config['rate_cell']] = self._rate(next(iter(bucket.rates)))
                elif len(bucket.rates) > 1:
                    cells[config['rate_cell']] = self._rate(self._default_rate(config['rate_cell']))
                    self._add_issue(
                        'multiple_rates_for_cell',
                        'warning',
                        'В одной строке формы обнаружено несколько ставок, применена ставка формы.',
                        line_key=line_key,
                        cell=config['rate_cell'],
                        rates=[self._rate(rate) for rate in sorted(bucket.rates)],
                    )
                else:
                    cells[config['rate_cell']] = self._rate(self._default_rate(config['rate_cell']))
                self._compute_formula_tax(cells, config['base_cell'], config['rate_cell'], config['tax_cell'], bucket=bucket)

        cells['059'] = self._money(Decimal(cells['055']) + Decimal(cells['058']))
        cells['066'] = self._money(Decimal(cells['062']) + Decimal(cells['065']))
        cells['073'] = self._money(Decimal(cells['069']) + Decimal(cells['072']))
        cells['080'] = self._money(Decimal(cells['076']) + Decimal(cells['079']))
        cells['169'] = self._money(Decimal(cells['165']) + Decimal(cells['168']))

        current_rows, current_amount_total, current_tax_total = self._advance_rows(self.current_period_advance_payments)
        previous_rows, previous_amount_total, previous_tax_total = self._advance_rows(self.previous_period_advance_offsets)

        cells[ADVANCE_CURRENT_TOTAL_AMOUNT_CELL] = self._money(current_amount_total)
        cells[ADVANCE_CURRENT_TOTAL_TAX_CELL] = self._money(current_tax_total)
        cells[ADVANCE_PREVIOUS_TOTAL_AMOUNT_CELL] = self._money(previous_amount_total)
        cells[ADVANCE_PREVIOUS_TOTAL_TAX_CELL] = self._money(previous_tax_total)

        total_base = sum((Decimal(cells[cell]) for cell in BASE_TOTAL_CELLS), ZERO) + current_amount_total - previous_amount_total
        total_tax = sum((Decimal(cells[cell]) for cell in TAX_TOTAL_CELLS), ZERO) + current_tax_total - previous_tax_total
        cells[TOTAL_BASE_CELL] = self._money(total_base)
        cells[TOTAL_TAX_CELL] = self._money(total_tax)

        ready_for_submission = not any(issue['severity'] == 'error' for issue in self.issues)

        return {
            'form_code': 'STI-091',
            'form_version': '9',
            'year': self.year,
            'quarter': self.quarter,
            'report_kind': self.report_kind,
            'period': {
                'start': date_from.isoformat(),
                'end': date_to.isoformat(),
            },
            'header': {
                '102': self.tin or TIN_PLACEHOLDER,
                '103': self.taxpayer_name or HEADER_PLACEHOLDER,
                '104': self.tax_office or HEADER_PLACEHOLDER,
                '104_code': self.tax_office_code,
                '104_name': self.tax_office_name,
                '105': self.contact_phone or PHONE_PLACEHOLDER,
                '115': self.contact_phone or PHONE_PLACEHOLDER,
            },
            'cells': {key: (str(value) if isinstance(value, bool) else value) for key, value in cells.items()},
            'advance_tables': {
                'current_period_advance_payments': current_rows,
                'previous_period_advance_offsets': previous_rows,
            },
            'ready_for_submission': ready_for_submission,
            'issues': self.issues,
        }
