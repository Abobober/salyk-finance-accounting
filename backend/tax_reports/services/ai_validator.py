import os
from pathlib import Path

from config.openrouter import OpenRouterError, create_chat_completion

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


class AITaxValidator:
    def __init__(self):
        base_dir = Path(__file__).resolve().parents[1]
        self.instructions_path = base_dir / "instructions" / "unified_tax_rules.pdf"

    def _load_instructions(self):
        if not self.instructions_path.exists() or PdfReader is None:
            return ""

        try:
            reader = PdfReader(str(self.instructions_path))
            return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        except Exception:
            return ""

    def validate(self, report_data):
        instructions = self._load_instructions()
        instruction_text = (
            instructions
            if instructions
            else "Инструкция не найдена, выполни проверку по базовым правилам КР."
        )

        prompt = f"""
Проверь корректность расчета единого налога КР строго по инструкции ниже.

Инструкция:
{instruction_text}

Данные:
{report_data}

Ответь:
1. Корректно ли?
2. Есть ли ошибки?
3. Краткое пояснение.
"""

        if not os.getenv("OPENROUTER_API_KEY"):
            return "AI-проверка недоступна: не задан OPENROUTER_API_KEY."

        try:
            return create_chat_completion(
                messages=[
                    {"role": "system", "content": "Ты налоговый аудитор КР."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                timeout=30,
            )
        except OpenRouterError as exc:
            return f"AI-проверка недоступна: {exc.message}"
