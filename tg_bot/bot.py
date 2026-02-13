"""
Обработчики бота: /start, привязка по коду, выбор дохода/расхода, ввод суммы, подтверждение.
"""
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
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
        ],
        resize_keyboard=True,
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="Отмена", callback_data="confirm_no"),
        ],
    ])


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
        "Код привязки можно получить в веб-кабинете (раздел «Профиль» или «Привязать Telegram»).\n\n"
        "Введите код:",
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


@router.message(TransactionStates.choose_type, F.text.in_(["Доход", "Расход"]))
async def choose_type(message: Message, state: FSMContext):
    transaction_type = "income" if message.text == "Доход" else "expense"
    await state.update_data(transaction_type=transaction_type)
    await state.set_state(TransactionStates.enter_amount)
    await message.answer("Введите сумму (например: 500 или 1250.50):")


@router.message(TransactionStates.choose_type, F.text)
async def choose_type_unknown(message: Message):
    await message.answer("Нажмите кнопку «Доход» или «Расход».", reply_markup=main_menu_kb())


@router.message(TransactionStates.enter_amount, F.text)
async def enter_amount(message: Message, state: FSMContext):
    amount_str = parse_amount(message.text)
    if not amount_str:
        await message.answer("Введите корректную сумму (положительное число, до двух знаков после запятой).")
        return

    data = await state.get_data()
    t_type = data.get("transaction_type", "expense")
    type_label = "Доход" if t_type == "income" else "Расход"

    await state.update_data(amount=amount_str)
    await state.set_state(TransactionStates.confirm)
    await message.answer(
        f"{type_label} — {amount_str} сом.\n\nПодтвердить?",
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

    telegram_id = str(callback.from_user.id)

    try:
        access_token, _ = await get_api().get_token_by_telegram_id(telegram_id)
        await get_api().create_transaction(
            access_token=access_token,
            transaction_type=transaction_type,
            amount=amount,
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


def build_dp(bot: Bot) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp
