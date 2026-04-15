import os
from pathlib import Path

import requests

for line in Path(__file__).resolve().parents[1].joinpath(".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        os.environ["OPENROUTER_API_KEY"] = line.split("=", 1)[1].strip()
        break

api_key = os.getenv("OPENROUTER_API_KEY")
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "finance-accounting",
}

data = {
    "model": "openrouter/free",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Ответь ровно: ok"},
    ],
    "temperature": 0.2,
}

response = requests.post(url, headers=headers, json=data, timeout=30)

print("HTTP статус:", response.status_code)

try:
    json_response = response.json()
    print("Ответ OpenRouter (JSON):")
    print(json_response)
except ValueError:
    print("OpenRouter вернул не JSON!")
    print(response.text)
