from pathlib import Path
from typing import Dict

from django.conf import settings


class TemplateNotFoundError(Exception):
    """Raised when no template is configured or file is missing for given params."""


BASE_DIR = Path(settings.BASE_DIR)
FORMS_ROOT = BASE_DIR / "FORMS"


def _scan_forms_directory() -> Dict[str, Dict[str, Path]]:
    """
    Автоматически сканирует каталог FORMS и собирает все доступные form.pdf.

    Возвращает структуру:
    {
        "STI-101": {"default": Path("FORMS/STI-101/form.pdf")},
        "STI-107": {"_07": Path("FORMS/STI-107/_07/form.pdf")},
        ...
    }
    """
    forms: Dict[str, Dict[str, Path]] = {}

    if not FORMS_ROOT.exists():
        return forms

    for form_dir in FORMS_ROOT.iterdir():
        if not form_dir.is_dir():
            continue

        code = form_dir.name  # e.g. "STI-107"
        versions: Dict[str, Path] = {}

        # Вариант без подкаталогов версий: FORMS/STI-101/form.pdf
        direct_form = form_dir / "form.pdf"
        if direct_form.exists():
            versions["default"] = Path("FORMS") / code / "form.pdf"

        # Варианты с версиями: FORMS/STI-107/_07/form.pdf
        for sub_dir in form_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            form_pdf = sub_dir / "form.pdf"
            if form_pdf.exists():
                versions[sub_dir.name] = Path("FORMS") / code / sub_dir.name / "form.pdf"

        if versions:
            forms[code] = versions

    return forms


# Все найденные в репозитории формы.
AVAILABLE_FORMS: Dict[str, Dict[str, Path]] = _scan_forms_directory()


def get_available_forms() -> Dict[str, Dict[str, Path]]:
    """
    Возвращает карту всех найденных форм и версий в каталоге FORMS.

    Ключи первого уровня — код формы (например, "STI-107"),
    второго уровня — версия ("default", "_07" и т.п.),
    значение — относительный путь от BASE_DIR.
    """
    return AVAILABLE_FORMS


def _normalize_form_code(report_type: str) -> str:
    """
    Приводит тип отчета к виду кода формы, например:
    - "sti_107" -> "STI-107"
    - "STI-101" -> "STI-101"
    """
    value = report_type.strip().upper()
    value = value.replace("_", "-")
    return value


def _auto_resolve_form_template(report_type: str, period_key: str) -> Path:
    """
    Автоматическое разрешение шаблона, если явная привязка не найдена.

    Предполагается, что report_type соответствует коду формы (STI-101 и т.п.).
    Если для формы несколько версий, по умолчанию выбираем:
    - если period_key совпадает с ключом версии — её,
    - иначе последнюю по алфавиту/номеру версию.
    """
    code = _normalize_form_code(report_type)
    form_versions = AVAILABLE_FORMS.get(code)

    if not form_versions:
        raise TemplateNotFoundError(
            f"No PDF template found for form code '{code}' in FORMS directory."
        )

    # Если явно указана версия через period_key и такая есть — используем её.
    if period_key in form_versions:
        relative_path = form_versions[period_key]
    else:
        # Иначе выбираем "самую новую" версию по имени ключа.
        # Для ключей вида "_03", "_06", "_07" это будет максимальное значение.
        selected_version_key = sorted(form_versions.keys())[-1]
        relative_path = form_versions[selected_version_key]

    absolute_path = BASE_DIR / relative_path
    if not absolute_path.exists():
        raise TemplateNotFoundError(
            f"PDF template file not found at path '{absolute_path}'. "
            "Please check that the form file is present in the project."
        )

    return absolute_path


# Явный конфиг сопоставления:
# report_type -> tax_regime -> period_key -> относительный путь до PDF шаблона.
# При добавлении новых типов отчетов/режимов/периодов достаточно обновить этот словарь,
# бизнес-логика при этом не меняется.
TAX_REPORT_TEMPLATES: Dict[str, Dict[str, Dict[str, Path]]] = {
    # Unified tax report for SINGLE tax regime, quarterly period.
    "unified_tax": {
        "single": {
            # Официальный бланк единого налога — форма STI-107, версия _07.
            # Если по какой-то причине форма не обнаружится в AVAILABLE_FORMS,
            # используем ожидаемый путь по умолчанию.
            "quarterly": AVAILABLE_FORMS.get("STI-107", {}).get(
                "_07", Path("FORMS") / "STI-107" / "_07" / "form.pdf"
            ),
        },
        # Дополнительные режимы (например, "general") можно добавить здесь позже.
    },
}


def get_template_path(report_type: str, tax_regime: str, period_key: str) -> Path:
    """
    Resolve absolute path to PDF template for given report parameters.

    :param report_type: Logical report type, e.g. "unified_tax" or "STI-107".
    :param tax_regime: Tax regime code from OrganizationProfile.TaxRegime, e.g. "single".
    :param period_key: Period identifier understood by business logic, e.g. "quarterly".
    :raises TemplateNotFoundError: when mapping or file is missing.
    :return: Absolute filesystem path to the PDF template.
    """
    # 1. Пытаемся использовать явный конфиг (тип/режим/период).
    try:
        relative_path = TAX_REPORT_TEMPLATES[report_type][tax_regime][period_key]
        absolute_path = BASE_DIR / relative_path
        if not absolute_path.exists():
            raise TemplateNotFoundError(
                f"PDF template file not found at path '{absolute_path}'. "
                "Please check that the form file is present in the project."
            )
        return absolute_path
    except KeyError:
        # 2. Если явной настройки нет, пробуем автоматически подобрать шаблон
        #    по коду формы (например, report_type == 'STI-101').
        return _auto_resolve_form_template(report_type, period_key)
