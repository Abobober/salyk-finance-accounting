import requests
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "stepfun/step-3.5-flash:free"


class AITaxValidator:

    def validate(self, report_data):

        prompt = f"""
        Проверь корректность расчета единого налога КР.

        Данные:
        {report_data}

        Ответь:
        1. Корректно ли?
        2. Есть ли ошибки?
        3. Краткое пояснение.
        """

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Ты налоговый аудитор КР."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(URL, headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]
