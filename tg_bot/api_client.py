"""
Клиент API Salyk Finance для бота.

Требует от бэкенда:
  - POST /api/bot/link/   — привязка по коду (code, telegram_id)
  - POST /api/bot/auth/  — выдача JWT по telegram_id (X-Bot-Secret)
Дальше бот использует стандартные эндпоинты с Bearer токеном.
"""
import os
from datetime import date
from typing import Optional

import aiohttp


class SalykBotAPIError(Exception):
    """Ошибка ответа API (4xx/5xx или бизнес-логика)."""
    def __init__(self, message: str, status: Optional[int] = None):
        self.message = message
        self.status = status
        super().__init__(message)


class SalykBotAPI:
    def __init__(
        self,
        base_url: str,
        bot_secret: Optional[str] = None,
    ):
        self.base = base_url.rstrip("/")
        self.bot_secret = bot_secret
        self._session: Optional[aiohttp.ClientSession] = None

    async def _session_get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def link_by_code(self, code: str, telegram_id: str) -> bool:
        """
        Привязать аккаунт по коду. Вызывает POST /api/bot/link/.
        Эндпоинт пока не реализован на бэкенде — при появлении раскомментировать.
        """
        # TODO: когда бэкенд добавит POST /api/bot/link/
        # payload = {"code": code.strip(), "telegram_id": str(telegram_id)}
        # headers = {}
        # if self.bot_secret:
        #     headers["X-Bot-Secret"] = self.bot_secret
        # async with (await self._session_get()).post(
        #     f"{self.base}/bot/link/",
        #     json=payload,
        #     headers=headers,
        # ) as resp:
        #     if resp.status == 200:
        #         return True
        #     data = await resp.json() if resp.content_type == "application/json" else {}
        #     raise SalykBotAPIError(
        #         data.get("detail", data.get("code", "Ошибка привязки")),
        #         status=resp.status,
        #     )
        raise SalykBotAPIError(
            "Привязка по коду пока недоступна. Нужно добавить на бэкенде POST /api/bot/link/"
        )

    async def get_token_by_telegram_id(self, telegram_id: str) -> tuple[str, Optional[str]]:
        """
        Получить access (и refresh) токен по telegram_id. Вызывает POST /api/bot/auth/.
        Эндпоинт пока не реализован на бэкенде — при появлении раскомментировать.
        """
        # TODO: когда бэкенд добавит POST /api/bot/auth/
        # payload = {"telegram_id": str(telegram_id)}
        # headers = {}
        # if self.bot_secret:
        #     headers["X-Bot-Secret"] = self.bot_secret
        # async with (await self._session_get()).post(
        #     f"{self.base}/bot/auth/",
        #     json=payload,
        #     headers=headers,
        # ) as resp:
        #     if resp.status != 200:
        #         data = await resp.json() if resp.content_type == "application/json" else {}
        #         raise SalykBotAPIError(
        #             data.get("detail", "Ошибка авторизации бота"),
        #             status=resp.status,
        #         )
        #     data = await resp.json()
        #     return data["access"], data.get("refresh")
        raise SalykBotAPIError(
            "Авторизация бота пока недоступна. Нужно добавить на бэкенде POST /api/bot/auth/"
        )

    async def create_transaction(
        self,
        access_token: str,
        transaction_type: str,
        amount: str,
        transaction_date: Optional[date] = None,
        payment_method: str = "cash",
        is_business: bool = False,
        is_taxable: bool = True,
        category_id: Optional[int] = None,
        description: str = "",
    ) -> dict:
        """
        POST /api/finance/transactions/ — создание транзакции.
        Используется после того, как бот получит access_token по telegram_id.
        """
        if transaction_date is None:
            transaction_date = date.today()
        payload = {
            "transaction_type": transaction_type,
            "amount": amount,
            "transaction_date": transaction_date.isoformat(),
            "payment_method": payment_method,
            "is_business": is_business,
            "is_taxable": is_taxable,
            "description": description or "Из Telegram-бота",
        }
        if category_id is not None:
            payload["category"] = category_id
        if is_business:
            payload["activity_code"] = None  # упрощённо; при необходимости передать id

        async with (await self._session_get()).post(
            f"{self.base}/finance/transactions/",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        ) as resp:
            if resp.status in (200, 201):
                return await resp.json()
            data = await resp.json() if resp.content_type == "application/json" else {}
            detail = data.get("detail")
            if isinstance(detail, dict):
                first = next(iter(detail.values()), None)
                msg = first[0] if isinstance(first, list) else str(first)
            else:
                msg = str(detail) if detail else "Ошибка создания транзакции"
            raise SalykBotAPIError(msg, status=resp.status)


def get_api_from_env() -> SalykBotAPI:
    base = os.getenv("API_BASE", "http://127.0.0.1:8000/api")
    secret = os.getenv("BOT_API_SECRET")
    return SalykBotAPI(base_url=base, bot_secret=secret)
