import requests
import os

api_key = os.getenv("OPENROUTER_API_KEY")
url = "https://openrouter.ai/v1/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "stepfun/step-3.5-flash:free",
    "messages": [{"role": "user", "content": "Привет, объясни AI простыми словами"}],
    "max_tokens": 50
}

response = requests.post(url, headers=headers, json=data)

print("HTTP статус:", response.status_code)

try:
    json_response = response.json()
    print("Ответ OpenRouter (JSON):")
    print(json_response)
except ValueError:
    print("OpenRouter вернул не JSON!")
    print(response.text)
