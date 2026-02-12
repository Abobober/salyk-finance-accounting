from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import os
from .serializers import ChatSessionSerializer
from .chat_sessions import get_history, append_history

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "stepfun/step-3.5-flash:free"


class OpenRouterView(GenericAPIView):
    """
    AI-Бухгалтер Кыргызстана с временной историей в RAM
    """
    permission_classes = [AllowAny]
    serializer_class = ChatSessionSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        session_id = serializer.validated_data["session_id"]

        # Получаем историю из RAM
        history = get_history(session_id)

        # Формируем сообщения для модели
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты профессиональный бухгалтер Кыргызстана с опытом более 15 лет. "
                    "Специализируешься на ИП и ОсОО. Отлично знаешь налоговое законодательство КР, "
                    "ГНС, отчетность, Единый налог, НДС, подоходный налог, соцфонд, страховые взносы, "
                    "ЭСФ, ЭТТН и электронные сервисы налоговой. "
                    "Отвечай структурировано, профессионально и строго по законам КР. "
                    "Если данных недостаточно — задай уточняющий вопрос."
                )
            }
        ]

        # Добавляем историю
        messages.extend(history)

        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": message})

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return Response(
                {"error": "Ошибка запроса к OpenRouter", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            data = response.json()
            assistant_reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError):
            return Response(
                {"error": "Некорректный ответ от OpenRouter", "raw": data},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Сохраняем сообщения в RAM
        append_history(session_id, "user", message)
        append_history(session_id, "assistant", assistant_reply)

        return Response(
            {
                "assistant": assistant_reply,
                "session_id": session_id
            },
            status=status.HTTP_200_OK
        )
