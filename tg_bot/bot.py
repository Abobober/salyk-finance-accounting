"""
Обработчики бота: /start, привязка по коду, выбор дохода/расхода, способ оплаты, категории, сумма, подтверждение.
"""
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from states import LinkStates, TransactionStates
from api_client import SalykBotAPI, SalykBotAPIError, get_api_from_env


router = Router()
api: SalykBotAPI | None = None


def get_api() -> SalykBotAPI:
    global api
    if api is None:
        api = get_api_from_env()
    return api


# --- Клавиатуры ---

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Доход"), KeyboardButton(text="Расход")],
            [KeyboardButton(text="Транзакции")],
            [KeyboardButton(text="Меню")],
        ],
        resize_keyboard=True,
    )


def payment_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Наличные"), KeyboardButton(text="Безнал")],
            [KeyboardButton(text="Меню")],
        ],
        resize_keyboard=True,
    )


def menu_only_kb() -> ReplyKeyboardMarkup:
    """Только кнопка Меню (для ввода суммы)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Меню")]],
        resize_keyboard=True,
    )


def confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение с кнопкой Изменить."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton(text="Отмена", callback_data="confirm_no"),
        ],
        [InlineKeyboardButton(text="Изменить", callback_data="confirm_edit")],
    ])


def confirm_edit_kb() -> InlineKeyboardMarkup:
    """Выбор что изменить."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Тип", callback_data="edit_type"),
            InlineKeyboardButton(text="Способ оплаты", callback_data="edit_payment"),
        ],
        [
            InlineKeyboardButton(text="Категория", callback_data="edit_category"),
            InlineKeyboardButton(text="Сумму", callback_data="edit_amount"),
        ],
        [InlineKeyboardButton(text="Назад", callback_data="edit_back")],
    ])


def transactions_list_kb(transactions: list[dict]) -> InlineKeyboardMarkup:
    """Кнопки удаления для каждой транзакции (до 10)."""
    buttons = []
    for t in transactions[:10]:
        tid = t.get("id")
        dt = (t.get("transaction_date") or "")[:10]
        amt = t.get("amount", 0)
        btn_text = f"🗑 {dt} {amt}"
        if len(btn_text) > 32:
            btn_text = f"🗑 {dt}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"del_{tid}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def delete_confirm_kb(tx_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, удалить", callback_data=f"del_yes_{tx_id}"),
            InlineKeyboardButton(text="Нет", callback_data="del_no"),
        ],
    ])


def category_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    """Кнопки категорий + Пропустить + Меню."""
    buttons = []
    for c in categories[:15]:  # максимум 15 кнопок
        buttons.append([InlineKeyboardButton(text=c["name"], callback_data=f"cat_{c['id']}")])
    buttons.append([
        InlineKeyboardButton(text="Пропустить", callback_data="cat_skip"),
        InlineKeyboardButton(text="Меню", callback_data="menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Валидация суммы ---

def parse_amount(text: str) -> str | None:
    """Допускаем целые и с запятой/точкой: 100, 100.50, 100,50."""
    text = text.strip().replace(",", ".")
    if not re.match(r"^\d+(\.\d{1,2})?$", text):
        return None
    try:
        v = float(text)
        if v <= 0:
            return None
        return f"{v:.2f}" if "." in text else f"{int(v)}.00"
    except ValueError:
        return None


# --- Handlers ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = str(message.from_user.id)

    # Проверяем, пришёл ли код из ссылки (t.me/bot?start=UUID)
    payload = (message.text or "").replace("/start", "").strip()

    if payload:
        try:
            await get_api().link_by_code(payload, telegram_id)
            await message.answer(
                "Аккаунт привязан. Теперь можно добавлять транзакции.\n\nВыберите тип операции:",
                reply_markup=main_menu_kb(),
            )
            await state.set_state(TransactionStates.choose_type)
        except SalykBotAPIError as e:
            await message.answer(f"Ошибка привязки: {e.message}\n\nСсылка могла истечь. Получите новую в веб-кабинете.")
        return

    try:
        token, _ = await get_api().get_token_by_telegram_id(telegram_id)
    except SalykBotAPIError:
        token = None

    if token:
        await message.answer(
            "Привет! Выберите тип операции:",
            reply_markup=main_menu_kb(),
        )
        await state.set_state(TransactionStates.choose_type)
        return

    await message.answer(
        "Чтобы пользоваться ботом, привяжите аккаунт Salyk Finance.\n\n"
        "Получите ссылку в веб-кабинете (Профиль → Привязать Telegram) и перейдите по ней.\n\n"
        "Или введите код вручную:",
    )
    await state.set_state(LinkStates.waiting_code)


@router.message(LinkStates.waiting_code, F.text)
async def handle_link_code(message: Message, state: FSMContext):
    code = message.text.strip()
    telegram_id = str(message.from_user.id)

    try:
        await get_api().link_by_code(code, telegram_id)
    except SalykBotAPIError as e:
        await message.answer(f"Ошибка привязки: {e.message}")
        return

    await state.clear()
    await state.set_state(TransactionStates.choose_type)
    await message.answer(
        "Аккаунт привязан. Теперь можно добавлять транзакции.\n\nВыберите тип операции:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Команда /menu — выход в главное меню."""
    await state.clear()
    telegram_id = str(message.from_user.id)
    try:
        await get_api().get_token_by_telegram_id(telegram_id)
    except SalykBotAPIError:
        await message.answer(
            "Чтобы пользоваться ботом, привяжите аккаунт Salyk Finance.\n\n"
            "Получите ссылку в веб-кабинете (Профиль → Привязать Telegram) и перейдите по ней.",
        )
        await state.set_state(LinkStates.waiting_code)
        return
    await state.set_state(TransactionStates.choose_type)
    await message.answer("Главное меню. Выберите тип операции:", reply_markup=main_menu_kb())


@router.message(F.text == "Меню")
async def btn_menu(message: Message, state: FSMContext):
    """Кнопка «Меню» — выход в главное меню из любого состояния."""
    await state.clear()
    telegram_id = str(message.from_user.id)
    try:
        await get_api().get_token_by_telegram_id(telegram_id)
    except SalykBotAPIError:
        await message.answer(
            "Чтобы пользоваться ботом, привяжите аккаунт Salyk Finance.\n\n"
            "Получите ссылку в веб-кабинете (Профиль → Привязать Telegram) и перейдите по ней.",
        )
        await state.set_state(LinkStates.waiting_code)
        return
    await state.set_state(TransactionStates.choose_type)
    await message.answer("Главное меню. Выберите тип операции:", reply_markup=main_menu_kb())


async def _send_transactions_list(message: Message, state: FSMContext | None = None, with_delete: bool = False) -> bool:
    """Отправить список транзакций. with_delete — добавить кнопки удаления."""
    telegram_id = str(message.from_user.id)
    try:
        access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
        transactions = await get_api().get_transactions(access_token, limit=15)
    except SalykBotAPIError as e:
        await message.answer(f"Не удалось загрузить транзакции: {e.message}")
        return False

    if not transactions:
        await message.answer("У вас пока нет транзакций. Добавьте первую — нажмите «Доход» или «Расход».")
        return False

    lines = ["📜 Последние транзакции (нажмите 🗑 для удаления):\n"] if with_delete else ["📜 Последние транзакции:\n"]
    type_emoji = {"income": "📈", "expense": "📉"}
    payment_short = {"cash": "нал", "non_cash": "безнал"}
    for t in transactions:
        tt = t.get("transaction_type", "")
        em = type_emoji.get(tt, "•")
        pm = payment_short.get(t.get("payment_method", "cash"), "")
        cat = t.get("category_name") or "—"
        amt = t.get("amount", 0)
        dt = t.get("transaction_date", "")[:10] if t.get("transaction_date") else ""
        lines.append(f"{em} {dt} | {amt} сом ({pm}) | {cat}")
    text = "\n".join(lines)
    reply_markup = transactions_list_kb(transactions) if with_delete else None
    await message.answer(text, reply_markup=reply_markup)
    if with_delete and state:
        await state.update_data(view_transactions_list=transactions)
        await state.set_state(TransactionStates.view_transactions)
    return True


@router.message(TransactionStates.choose_type, F.text == "Транзакции")
async def show_transactions(message: Message, state: FSMContext):
    """Показать список последних транзакций с кнопками удаления."""
    await _send_transactions_list(message, state, with_delete=True)


@router.callback_query(TransactionStates.view_transactions, F.data.startswith("del_"))
async def transaction_delete_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "del_no":
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        telegram_id = str(callback.from_user.id)
        try:
            access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
            transactions = await get_api().get_transactions(access_token, limit=15)
        except SalykBotAPIError:
            await state.set_state(TransactionStates.choose_type)
            await callback.message.answer("Выберите тип операции:", reply_markup=main_menu_kb())
            return
        lines = ["📜 Последние транзакции (нажмите 🗑 для удаления):\n"]
        type_emoji = {"income": "📈", "expense": "📉"}
        payment_short = {"cash": "нал", "non_cash": "безнал"}
        for t in transactions:
            tt, pm = t.get("transaction_type", ""), payment_short.get(t.get("payment_method", "cash"), "")
            em, cat = type_emoji.get(tt, "•"), t.get("category_name") or "—"
            dt = (t.get("transaction_date") or "")[:10]
            lines.append(f"{em} {dt} | {t.get('amount', 0)} сом ({pm}) | {cat}")
        await callback.message.edit_text("\n".join(lines), reply_markup=transactions_list_kb(transactions))
        await state.update_data(view_transactions_list=transactions)
        return

    if callback.data.startswith("del_yes_"):
        tx_id = int(callback.data.replace("del_yes_", ""))
        telegram_id = str(callback.from_user.id)
        try:
            access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
            await get_api().delete_transaction(access_token, tx_id)
        except SalykBotAPIError as e:
            await callback.message.answer(f"Ошибка: {e.message}")
            return
        try:
            access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
            transactions = await get_api().get_transactions(access_token, limit=15)
        except SalykBotAPIError:
            transactions = []
        lines = ["✅ Удалено.\n\n📜 Последние транзакции (нажмите 🗑 для удаления):\n"]
        if transactions:
            type_emoji = {"income": "📈", "expense": "📉"}
            payment_short = {"cash": "нал", "non_cash": "безнал"}
            for t in transactions:
                tt, pm = t.get("transaction_type", ""), payment_short.get(t.get("payment_method", "cash"), "")
                em, cat = type_emoji.get(tt, "•"), t.get("category_name") or "—"
                dt = (t.get("transaction_date") or "")[:10]
                lines.append(f"{em} {dt} | {t.get('amount', 0)} сом ({pm}) | {cat}")
            await callback.message.edit_text("\n".join(lines), reply_markup=transactions_list_kb(transactions))
            await state.update_data(view_transactions_list=transactions)
        else:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            await callback.message.edit_text("✅ Транзакция удалена. Список пуст.")
            await state.set_state(TransactionStates.choose_type)
            await callback.message.answer("Выберите тип операции:", reply_markup=main_menu_kb())
        return

    # del_{id} — показать подтверждение
    tx_id = int(callback.data.replace("del_", ""))
    data = await state.get_data()
    txs = data.get("view_transactions_list") or []
    t = next((x for x in txs if x.get("id") == tx_id), None)
    if not t:
        await callback.answer("Транзакция не найдена.")
        return
    dt = (t.get("transaction_date") or "")[:10]
    amt = t.get("amount", 0)
    cat = t.get("category_name") or "—"
    await callback.message.edit_text(
        f"Удалить транзакцию?\n\n• {dt} | {amt} сом | {cat}",
        reply_markup=delete_confirm_kb(tx_id),
    )


@router.message(TransactionStates.choose_type, F.text.in_(["Доход", "Расход"]))
async def choose_type(message: Message, state: FSMContext):
    transaction_type = "income" if message.text == "Доход" else "expense"
    await state.update_data(transaction_type=transaction_type)
    await state.set_state(TransactionStates.choose_payment)
    await message.answer("Выберите способ оплаты:", reply_markup=payment_kb())


@router.message(TransactionStates.choose_type, F.text)
async def choose_type_unknown(message: Message):
    await message.answer("Нажмите кнопку «Доход» или «Расход».", reply_markup=main_menu_kb())


@router.message(TransactionStates.choose_payment, F.text.in_(["Наличные", "Безнал"]))
async def choose_payment(message: Message, state: FSMContext):
    payment_method = "cash" if message.text == "Наличные" else "non_cash"
    await state.update_data(payment_method=payment_method)
    await state.set_state(TransactionStates.choose_category)

    data = await state.get_data()
    t_type = data.get("transaction_type", "expense")
    telegram_id = str(message.from_user.id)

    try:
        access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
        categories = await get_api().get_categories(access_token, category_type=t_type)
    except SalykBotAPIError as e:
        await message.answer(f"Не удалось загрузить категории: {e.message}. Выберите категорию позже или пропустите.")
        categories = []

    if not categories:
        await state.update_data(category_id=None, category_name=None, categories_cache=None)
        await state.set_state(TransactionStates.enter_amount)
        await message.answer("Введите сумму (например: 500 или 1250.50):", reply_markup=menu_only_kb())
        return

    await state.update_data(categories_cache={c["id"]: c["name"] for c in categories})
    await message.answer("Выберите категорию или пропустите:", reply_markup=category_kb(categories))


@router.message(TransactionStates.choose_payment, F.text)
async def choose_payment_unknown(message: Message):
    await message.answer("Нажмите «Наличные» или «Безнал».", reply_markup=payment_kb())


@router.callback_query(TransactionStates.choose_category, F.data == "menu")
async def category_callback_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.clear()
    await state.set_state(TransactionStates.choose_type)
    await callback.message.answer("Главное меню. Выберите тип операции:", reply_markup=main_menu_kb())


@router.callback_query(TransactionStates.choose_category, F.data.startswith("cat_"))
async def choose_category_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if callback.data == "cat_skip":
        await state.update_data(category_id=None, category_name=None)
    else:
        cat_id = int(callback.data.replace("cat_", ""))
        data = await state.get_data()
        cache = data.get("categories_cache") or {}
        cat_name = cache.get(cat_id)
        await state.update_data(category_id=cat_id, category_name=cat_name)

    await state.set_state(TransactionStates.enter_amount)
    await callback.message.answer("Введите сумму (например: 500 или 1250.50):", reply_markup=menu_only_kb())


def _format_confirm_text(data: dict) -> str:
    """Формирует детальный текст для подтверждения."""
    from datetime import date
    t_type = data.get("transaction_type", "expense")
    type_label = "Доход" if t_type == "income" else "Расход"
    amount = data.get("amount", "0")
    payment = data.get("payment_method", "cash")
    payment_label = "Наличные" if payment == "cash" else "Безнал"
    cat_name = data.get("category_name") or "—"
    t_date = data.get("transaction_date") or date.today().isoformat()
    return (
        "📋 Детали транзакции:\n\n"
        f"• Тип: {type_label}\n"
        f"• Сумма: {amount} сом\n"
        f"• Способ оплаты: {payment_label}\n"
        f"• Категория: {cat_name}\n"
        f"• Дата: {t_date}\n\n"
        "Всё верно? Подтвердите или нажмите «Изменить»."
    )


@router.message(TransactionStates.enter_amount, F.text)
async def enter_amount(message: Message, state: FSMContext):
    amount_str = parse_amount(message.text)
    if not amount_str:
        await message.answer("Введите корректную сумму (положительное число, до двух знаков после запятой).")
        return

    from datetime import date
    await state.update_data(amount=amount_str, transaction_date=date.today().isoformat())
    await state.set_state(TransactionStates.confirm)
    data = await state.get_data()
    await message.answer(
        _format_confirm_text(data),
        reply_markup=confirm_kb(),
    )


@router.callback_query(TransactionStates.confirm, F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    data = await state.get_data()
    transaction_type = data.get("transaction_type", "expense")
    amount = data.get("amount", "0")
    payment_method = data.get("payment_method", "cash")
    category_id = data.get("category_id")

    telegram_id = str(callback.from_user.id)

    try:
        access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
        await get_api().create_transaction(
            access_token=access_token,
            transaction_type=transaction_type,
            amount=amount,
            payment_method=payment_method,
            category_id=category_id,
        )
    except SalykBotAPIError as e:
        await callback.message.answer(f"Не удалось создать транзакцию: {e.message}")
        await state.set_state(TransactionStates.choose_type)
        await callback.message.answer("Выберите тип операции:", reply_markup=main_menu_kb())
        return

    await state.set_state(TransactionStates.choose_type)
    await callback.message.answer(
        "Транзакция добавлена. Она отобразится в веб-кабинете.\n\nДобавить ещё или выйти в меню — нажмите кнопку:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(TransactionStates.confirm, F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(TransactionStates.choose_type)
    await callback.message.answer("Отменено. Выберите тип операции:", reply_markup=main_menu_kb())


@router.callback_query(TransactionStates.confirm, F.data == "confirm_edit")
async def confirm_edit(callback: CallbackQuery, state: FSMContext):
    """Показать меню выбора что изменить."""
    await callback.answer()
    await callback.message.edit_text(
        "Что хотите изменить?",
        reply_markup=confirm_edit_kb(),
    )


@router.callback_query(TransactionStates.confirm, F.data == "edit_back")
async def edit_back(callback: CallbackQuery, state: FSMContext):
    """Вернуться к подтверждению."""
    await callback.answer()
    data = await state.get_data()
    await callback.message.edit_text(
        _format_confirm_text(data),
        reply_markup=confirm_kb(),
    )


@router.callback_query(TransactionStates.confirm, F.data == "edit_type")
async def edit_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(TransactionStates.edit_type)
    await callback.message.answer("Выберите тип операции:", reply_markup=main_menu_kb())


@router.message(TransactionStates.edit_type, F.text == "Транзакции")
async def edit_type_transactions(message: Message, state: FSMContext):
    await _send_transactions_list(message, with_delete=False)
    await message.answer("Выберите тип операции:", reply_markup=main_menu_kb())


@router.message(TransactionStates.edit_type, F.text.in_(["Доход", "Расход"]))
async def edit_type_pick(message: Message, state: FSMContext):
    t = "income" if message.text == "Доход" else "expense"
    await state.update_data(transaction_type=t)
    await state.set_state(TransactionStates.confirm)
    data = await state.get_data()
    await message.answer(_format_confirm_text(data), reply_markup=confirm_kb())


@router.message(TransactionStates.edit_type, F.text)
async def edit_type_unknown(message: Message):
    await message.answer("Нажмите «Доход» или «Расход» для изменения типа.", reply_markup=main_menu_kb())


@router.callback_query(TransactionStates.confirm, F.data == "edit_payment")
async def edit_payment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(TransactionStates.edit_payment)
    await callback.message.answer("Выберите способ оплаты:", reply_markup=payment_kb())


@router.message(TransactionStates.edit_payment, F.text.in_(["Наличные", "Безнал"]))
async def edit_payment_pick(message: Message, state: FSMContext):
    pm = "cash" if message.text == "Наличные" else "non_cash"
    await state.update_data(payment_method=pm)
    await state.set_state(TransactionStates.confirm)
    data = await state.get_data()
    await message.answer(_format_confirm_text(data), reply_markup=confirm_kb())


@router.message(TransactionStates.edit_payment, F.text)
async def edit_payment_unknown(message: Message):
    await message.answer("Нажмите «Наличные» или «Безнал».", reply_markup=payment_kb())


@router.callback_query(TransactionStates.confirm, F.data == "edit_category")
async def edit_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(TransactionStates.edit_category)
    data = await state.get_data()
    t_type = data.get("transaction_type", "expense")
    telegram_id = str(callback.from_user.id)
    try:
        access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
        categories = await get_api().get_categories(access_token, category_type=t_type)
    except SalykBotAPIError as e:
        await callback.message.answer(f"Не удалось загрузить категории: {e.message}")
        await state.set_state(TransactionStates.confirm)
        return
    if not categories:
        await state.update_data(category_id=None, category_name=None)
        await state.set_state(TransactionStates.confirm)
        data = await state.get_data()
        await callback.message.answer(_format_confirm_text(data), reply_markup=confirm_kb())
        return
    await state.update_data(categories_cache={c["id"]: c["name"] for c in categories})
    await callback.message.answer("Выберите категорию:", reply_markup=category_kb(categories))


@router.callback_query(TransactionStates.edit_category, F.data == "menu")
async def edit_category_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.clear()
    await state.set_state(TransactionStates.choose_type)
    await callback.message.answer("Главное меню. Выберите тип операции:", reply_markup=main_menu_kb())


@router.callback_query(TransactionStates.edit_category, F.data.startswith("cat_"))
async def edit_category_pick(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if callback.data == "cat_skip":
        await state.update_data(category_id=None, category_name=None)
    else:
        cat_id = int(callback.data.replace("cat_", ""))
        data = await state.get_data()
        cache = data.get("categories_cache") or {}
        await state.update_data(category_id=cat_id, category_name=cache.get(cat_id))
    await state.set_state(TransactionStates.confirm)
    data = await state.get_data()
    await callback.message.answer(_format_confirm_text(data), reply_markup=confirm_kb())


@router.callback_query(TransactionStates.confirm, F.data == "edit_amount")
async def edit_amount(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await state.set_state(TransactionStates.edit_amount)
    await callback.message.answer("Введите сумму (например: 500 или 1250.50):", reply_markup=menu_only_kb())


@router.message(TransactionStates.edit_amount, F.text)
async def edit_amount_pick(message: Message, state: FSMContext):
    amount_str = parse_amount(message.text)
    if not amount_str:
        await message.answer("Введите корректную сумму.")
        return
    await state.update_data(amount=amount_str)
    await state.set_state(TransactionStates.confirm)
    data = await state.get_data()
    await message.answer(_format_confirm_text(data), reply_markup=confirm_kb())


def build_dp(bot: Bot) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp
