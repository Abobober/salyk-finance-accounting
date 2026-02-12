from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import json
import os

from .serializers import ChatSerializer

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "stepfun/step-3.5-flash:free"


class OpenRouterView(GenericAPIView):
    """
    View для общения с OpenRouter через модель stepfun/step-3.5-flash:free
    """
    permission_classes = [AllowAny]
    serializer_class = ChatSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]

        messages = [{"role": "user", "content": user_message}]

        previous_assistant = serializer.validated_data.get("previous_assistant")
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
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Ошибка запроса к OpenRouter", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            data = response.json()
        except ValueError:
            return Response(
                {
                    "error": "OpenRouter вернул не JSON",
                    "status_code": response.status_code,
                    "content": response.text[:1000]
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        try:
            assistant_message = data["choices"][0]["message"]
        except (KeyError, IndexError):
            return Response(
                {"error": "Не удалось получить ответ модели", "raw_response": data},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({"assistant": assistant_message}, status=status.HTTP_200_OK)
