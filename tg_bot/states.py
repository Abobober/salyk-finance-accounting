"""
FSM-состояния для сценария добавления транзакции.
"""
from aiogram.fsm.state import State, StatesGroup


class LinkStates(StatesGroup):
    """Привязка аккаунта по коду."""
    waiting_code = State()


class TransactionStates(StatesGroup):
    """Добавление транзакции: тип → способ оплаты → категория → сумма → подтверждение."""
    choose_type = State()
    choose_payment = State()
    choose_category = State()
    enter_amount = State()
    confirm = State()
    # Режим редактирования — возврат в confirm после выбора
    edit_type = State()
    edit_payment = State()
    edit_category = State()
    edit_amount = State()
    # Просмотр транзакций с возможностью удаления
    view_transactions = State()
