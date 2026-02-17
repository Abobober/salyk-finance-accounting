import os
from pathlib import Path

import requests

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "stepfun/step-3.5-flash:free"


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

        if not OPENROUTER_API_KEY:
            return "AI-проверка недоступна: не задан OPENROUTER_API_KEY."

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Ты налоговый аудитор КР."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as exc:
            return f"AI-проверка недоступна: ошибка запроса к OpenRouter ({exc})."
        except (KeyError, IndexError, TypeError, ValueError):
            return "AI-проверка недоступна: неожиданный формат ответа OpenRouter."
