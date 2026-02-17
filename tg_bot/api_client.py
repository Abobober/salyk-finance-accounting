"""
Клиент API Salyk Finance для бота.
Использует /api/telegram/bot/link/ и /api/telegram/bot/auth/ (X-Bot-Secret).
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

    def _bot_headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.bot_secret:
            h["X-Bot-Secret"] = self.bot_secret
        return h

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def link_by_code(self, code: str, telegram_id: str) -> bool:
        """Привязать аккаунт по коду. POST /api/telegram/bot/link/"""
        payload = {"code": code.strip(), "telegram_id": str(telegram_id)}
        async with (await self._session_get()).post(
            f"{self.base}/telegram/bot/link/",
            json=payload,
            headers=self._bot_headers(),
        ) as resp:
            if resp.status == 200:
                return True
            data = await resp.json() if resp.content_type == "application/json" else {}
            raise SalykBotAPIError(
                data.get("detail", "Ошибка привязки"),
                status=resp.status,
            )

    async def get_token_by_telegram_id(self, telegram_id: str) -> tuple[str, Optional[str]]:
        """Получить JWT по telegram_id. POST /api/telegram/bot/auth/"""
        payload = {"telegram_id": str(telegram_id)}
        async with (await self._session_get()).post(
            f"{self.base}/telegram/bot/auth/",
            json=payload,
            headers=self._bot_headers(),
        ) as resp:
            if resp.status != 200:
                data = await resp.json() if resp.content_type == "application/json" else {}
                raise SalykBotAPIError(
                    data.get("detail", "Аккаунт не привязан"),
                    status=resp.status,
                )
            data = await resp.json()
            return data["access"], data.get("refresh")

    async def get_categories(self, access_token: str, category_type: Optional[str] = None) -> list[dict]:
        """
        GET /api/finance/categories/ — список категорий пользователя.
        category_type: 'income' | 'expense' — фильтр по типу.
        """
        params = {}
        if category_type:
            params["category_type"] = category_type
        async with (await self._session_get()).get(
            f"{self.base}/finance/categories/",
            params=params or None,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        ) as resp:
            if resp.status != 200:
                data = await resp.json() if resp.content_type == "application/json" else {}
                raise SalykBotAPIError(
                    data.get("detail", "Не удалось загрузить категории"),
                    status=resp.status,
                )
            data = await resp.json()
            items = data if isinstance(data, list) else data.get("results", data.get("data", []))
            if category_type:
                items = [c for c in items if c.get("category_type") == category_type]
            return items

    async def get_transactions(
        self,
        access_token: str,
        limit: int = 20,
        offset: int = 0,
        transaction_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict]:
        """
        GET /api/finance/transactions/ — список транзакций пользователя.
        """
        params = {"limit": limit, "offset": offset}
        if transaction_type:
            params["transaction_type"] = transaction_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        async with (await self._session_get()).get(
            f"{self.base}/finance/transactions/",
            params=params,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        ) as resp:
            if resp.status != 200:
                data = await resp.json() if resp.content_type == "application/json" else {}
                raise SalykBotAPIError(
                    data.get("detail", "Не удалось загрузить транзакции"),
                    status=resp.status,
                )
            data = await resp.json()
            items = data if isinstance(data, list) else data.get("results", data.get("data", []))
            return items

    async def delete_transaction(self, access_token: str, transaction_id: int) -> None:
        """DELETE /api/finance/transactions/:id/"""
        async with (await self._session_get()).delete(
            f"{self.base}/finance/transactions/{transaction_id}/",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        ) as resp:
            if resp.status not in (200, 204):
                data = await resp.json() if resp.content_type == "application/json" else {}
                raise SalykBotAPIError(
                    data.get("detail", "Не удалось удалить транзакцию"),
                    status=resp.status,
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
        amount_num = float(amount) if isinstance(amount, str) else amount
        payload = {
            "transaction_type": transaction_type,
            "amount": amount_num,
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
