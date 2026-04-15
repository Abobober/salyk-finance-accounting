import json

import requests
from django.conf import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _candidate_models():
    configured = getattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    fallbacks = getattr(settings, "OPENROUTER_FALLBACK_MODELS", [])
    models = [configured, *fallbacks]

    unique_models = []
    for model in models:
        if model and model not in unique_models:
            unique_models.append(model)
    return unique_models


def _extract_error_message(response):
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:500] if text else f"HTTP {response.status_code}"

    if not isinstance(payload, dict):
        return str(payload)

    error = payload.get("error")
    if isinstance(error, dict):
        parts = []
        message = error.get("message")
        if message:
            parts.append(str(message))

        metadata = error.get("metadata")
        if isinstance(metadata, dict):
            raw = metadata.get("raw")
            if raw:
                parts.append(str(raw))

        if parts:
            return " ".join(parts)

    for key in ("detail", "message", "error"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return json.dumps(payload, ensure_ascii=False)[:500]


def _extract_assistant_text(payload):
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter вернул неожиданный формат ответа.", status_code=502) from exc

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                text_parts.append(str(item["text"]))
        if text_parts:
            return "\n".join(text_parts)

    raise OpenRouterError("OpenRouter вернул пустой ответ модели.", status_code=502)


def create_chat_completion(messages, temperature=0.2, timeout=60):
    api_key = getattr(settings, "OPENROUTER_API_KEY", "")
    if not api_key:
        raise OpenRouterError("Не задан OPENROUTER_API_KEY.", status_code=503)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": getattr(settings, "OPENROUTER_SITE_URL", "http://localhost"),
        "X-Title": getattr(settings, "OPENROUTER_APP_NAME", "finance-accounting"),
    }

    errors = []
    candidate_models = _candidate_models()
    retryable_statuses = {429, 500, 502, 503, 504}

    for index, model in enumerate(candidate_models):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            errors.append(f"{model}: ошибка сети ({exc})")
            if index < len(candidate_models) - 1:
                continue
            raise OpenRouterError(
                "AI-сервис временно недоступен: не удалось связаться с OpenRouter.",
                status_code=503,
            ) from exc

        if response.ok:
            try:
                data = response.json()
            except ValueError as exc:
                raise OpenRouterError("OpenRouter вернул не JSON-ответ.", status_code=502) from exc
            return _extract_assistant_text(data)

        error_message = _extract_error_message(response)
        errors.append(f"{model}: {error_message}")
        if response.status_code in retryable_statuses and index < len(candidate_models) - 1:
            continue

        raise OpenRouterError(
            f"AI-сервис недоступен: {error_message}",
            status_code=503 if response.status_code in retryable_statuses else response.status_code,
        )

    summary = errors[-1] if errors else "неизвестная ошибка"
    raise OpenRouterError(
        f"AI-сервис временно недоступен: {summary}",
        status_code=503,
    )
