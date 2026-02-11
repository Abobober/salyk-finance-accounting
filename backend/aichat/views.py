from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # <-- добавлено
import requests
import json
import os

# Твой OpenRouter API ключ
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "stepfun/step-3.5-flash:free"

class OpenRouterView(APIView):
    """
    View для общения с OpenRouter через модель stepfun/step-3.5-flash:free
    """
    permission_classes = [AllowAny]  # <-- делаем view открытым

    def post(self, request):
        user_message = request.data.get("message")
        if not user_message:
            return Response(
                {"error": "Сообщение пользователя не предоставлено"},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = [{"role": "user", "content": user_message}]

        # Если пользователь передал предыдущие reasoning_details, добавляем их
        previous_assistant = request.data.get("previous_assistant")
        if previous_assistant:
            messages.append(previous_assistant)

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "reasoning": {"enabled": True}
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload))
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Ошибка запроса к OpenRouter", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            data = response.json()
        except ValueError:
            # OpenRouter вернул HTML или другой текст
            return Response(
                {
                    "error": "OpenRouter вернул не JSON",
                    "status_code": response.status_code,
                    "content": response.text[:1000]  # первые 1000 символов для безопасности
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Берём ответ модели
        try:
            assistant_message = data['choices'][0]['message']
        except (KeyError, IndexError):
            return Response(
                {"error": "Не удалось получить ответ модели", "raw_response": data},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({"assistant": assistant_message})
