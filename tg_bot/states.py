"""
FSM-состояния для сценария добавления транзакции.
"""
from aiogram.fsm.state import State, StatesGroup


class LinkStates(StatesGroup):
    """Привязка аккаунта по коду."""
    waiting_code = State()


class TransactionStates(StatesGroup):
    """Добавление транзакции: тип → сумма → подтверждение."""
    choose_type = State()
    enter_amount = State()
    confirm = State()
