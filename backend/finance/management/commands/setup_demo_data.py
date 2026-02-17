# python manage.py setup_demo_data --user admin@example.com --transactions 100

"""
Management command для создания демо-данных: категории и транзакции.
Использование: python manage.py setup_demo_data [--user USERNAME] [--transactions N]
"""
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from finance.models import Category, Transaction

User = get_user_model()


# Текстовые данные для категорий (расширенный набор)
EXPENSE_CATEGORIES = [
    'Продукты', 'Транспорт', 'Коммунальные услуги', 'Аренда',
    'Зарплата сотрудникам', 'Реклама и маркетинг', 'Оборудование',
    'Канцелярия', 'Интернет и связь', 'Прочие расходы',
    'Налоги', 'Страховка', 'Обучение', 'Медицина', 'Подписки'
]

INCOME_CATEGORIES = [
    'Продажа товаров', 'Оказание услуг', 'Аванс',
    'Инвестиции', 'Прочие доходы', 'Возврат', 'Дивиденды'
]

# Текстовые данные для описаний транзакций
EXPENSE_DESCRIPTIONS = [
    'Закупка продуктов для офиса', 'Такси до клиента', 'Оплата электричества',
    'Аренда помещения за месяц', 'Зарплата менеджера', 'Рекламная кампания в соцсетях',
    'Новый ноутбук для сотрудника', 'Бумага и картриджи', 'Интернет провайдер',
    'Разовые расходы', 'УСН за квартал', 'Страховка оборудования',
    'Курсы повышения квалификации', 'Медосмотр сотрудников', 'Подписка на сервис'
]

INCOME_DESCRIPTIONS = [
    'Продажа товара клиенту', 'Консультационные услуги', 'Предоплата от заказчика',
    'Доход от вложений', 'Прочий доход', 'Возврат от поставщика',
    'Выплата дивидендов'
]

# Описания без привязки к категории (универсальные)
GENERIC_DESCRIPTIONS = [
    'Оплата по счету', 'Ежемесячный платеж', 'Разовый платеж',
    'Оплата услуг', 'Закупка материалов', 'Выручка за день'
]


def get_random_date(days_back: int = 90) -> date:
    """Случайная дата за последние N дней."""
    return date.today() - timedelta(days=random.randint(0, days_back))


class Command(BaseCommand):
    help = 'Создает демо-данные: категории и транзакции для тестирования'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email пользователя, для которого создавать транзакции (по умолчанию первый пользователь)',
        )
        parser.add_argument(
            '--transactions',
            type=int,
            default=50,
            help='Количество транзакций для создания (по умолчанию 50)',
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Создать только категории, без транзакций',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='За какой период создавать транзакции в днях (по умолчанию 90)',
        )
        parser.add_argument(
            '--skip-if-populated',
            action='store_true',
            help='Пропустить создание транзакций, если у пользователя уже есть транзакции',
        )

    def handle(self, *args, **options):
        # 1. Создаём категории
        categories_created = self._create_categories()
        self.stdout.write(self.style.SUCCESS(f'Категории: создано {categories_created} новых.'))

        if options['categories_only']:
            return

        # 2. Создаём транзакции
        user = self._get_user(options['user'])
        if not user:
            self.stdout.write(self.style.WARNING('Пользователи не найдены. Создайте пользователя для генерации транзакций.'))
            return

        if options.get('skip_if_populated') and Transaction.objects.filter(user=user).exists():
            self.stdout.write(self.style.SUCCESS(f'У пользователя {user.email} уже есть транзакции. Пропуск.'))
            return

        transactions_created = self._create_transactions(
            user=user,
            count=options['transactions'],
            days_back=options['days'],
        )
        self.stdout.write(self.style.SUCCESS(f'Транзакции: создано {transactions_created} для пользователя {user.email}.'))

    def _create_categories(self) -> int:
        """Создаёт системные категории, если их ещё нет."""
        count = 0
        for name in EXPENSE_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=name,
                category_type=Category.CategoryType.EXPENSE,
                is_system=True,
                defaults={'user': None}
            )
            if created:
                count += 1

        for name in INCOME_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=name,
                category_type=Category.CategoryType.INCOME,
                is_system=True,
                defaults={'user': None}
            )
            if created:
                count += 1

        return count

    def _get_user(self, email: str | None):
        """Возвращает пользователя по email или первого в БД."""
        if email:
            return User.objects.filter(email=email).first()
        return User.objects.first()

    def _create_transactions(self, user, count: int, days_back: int) -> int:
        """Создаёт случайные транзакции для пользователя."""
        expense_cats = list(Category.objects.filter(
            category_type=Category.CategoryType.EXPENSE,
            is_system=True
        ))
        income_cats = list(Category.objects.filter(
            category_type=Category.CategoryType.INCOME,
            is_system=True
        ))

        if not expense_cats or not income_cats:
            self.stdout.write(self.style.WARNING('Нет категорий для транзакций. Сначала выполните setup_categories.'))
            return 0

        payment_methods = [
            Transaction.PaymentMethod.CASH,
            Transaction.PaymentMethod.NON_CASH,
        ]

        created = 0
        for _ in range(count):
            is_income = random.random() < 0.4  # 40% доходов, 60% расходов
            if is_income:
                category = random.choice(income_cats)
                amount = random.randint(500, 150000) / 100
                descriptions = INCOME_DESCRIPTIONS + GENERIC_DESCRIPTIONS
            else:
                category = random.choice(expense_cats)
                amount = random.randint(100, 80000) / 100
                descriptions = EXPENSE_DESCRIPTIONS + GENERIC_DESCRIPTIONS

            description = random.choice(descriptions)
            if len(description) > 100:
                description = description[:100]

            Transaction.objects.create(
                user=user,
                category=category,
                transaction_type=Transaction.TransactionType.INCOME if is_income else Transaction.TransactionType.EXPENSE,
                amount=amount,
                description=description,
                transaction_date=get_random_date(days_back),
                payment_method=random.choice(payment_methods),
                is_business=random.random() < 0.9,
                is_taxable=True,
                activity_code=None,
            )
            created += 1

        return created
