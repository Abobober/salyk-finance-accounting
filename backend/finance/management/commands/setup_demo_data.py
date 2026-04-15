# python manage.py setup_demo_data --user demo@example.com --transactions 100

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from finance.models import Category, Transaction
from organization.models import OrganizationActivity

User = get_user_model()


EXPENSE_CATEGORIES = [
    'Office supplies', 'Transport', 'Utilities', 'Rent', 'Payroll',
    'Marketing', 'Equipment', 'Stationery', 'Internet', 'Misc expenses',
    'Taxes', 'Insurance', 'Training', 'Healthcare', 'Subscriptions',
]

INCOME_CATEGORIES = [
    'Product sales', 'Services', 'Advance payment', 'Investments',
    'Other income', 'Refund', 'Dividends',
]

EXPENSE_DESCRIPTIONS = [
    'Office supplies purchase', 'Taxi to client', 'Electricity payment',
    'Monthly rent', 'Manager salary', 'Social media campaign',
    'New laptop', 'Paper and cartridges', 'Internet provider',
    'One-time expense', 'Quarterly tax payment', 'Equipment insurance',
    'Training course', 'Employee medical check', 'Service subscription',
]

INCOME_DESCRIPTIONS = [
    'Product sale', 'Consulting services', 'Customer prepayment',
    'Investment income', 'Other income', 'Supplier refund', 'Dividend payout',
]

GENERIC_DESCRIPTIONS = [
    'Invoice payment', 'Monthly payment', 'One-time payment',
    'Service payment', 'Materials purchase', 'Daily revenue',
]


def get_random_date(days_back: int = 90) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


class Command(BaseCommand):
    help = 'Create demo categories and transactions for local development'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Email of the user that will receive demo transactions')
        parser.add_argument('--transactions', type=int, default=50, help='Number of demo transactions to create')
        parser.add_argument('--categories-only', action='store_true', help='Create only categories')
        parser.add_argument('--days', type=int, default=90, help='How many days back demo transactions may be created')
        parser.add_argument('--skip-if-populated', action='store_true', help='Skip transaction creation when user already has data')

    def handle(self, *args, **options):
        categories_created = self._create_categories()
        self.stdout.write(self.style.SUCCESS(f'Categories created: {categories_created}'))

        if options['categories_only']:
            return

        user = self._get_user(options['user'])
        if not user:
            self.stdout.write(self.style.WARNING('No users found. Create a user before generating demo transactions.'))
            return

        if options.get('skip_if_populated') and Transaction.objects.filter(user=user).exists():
            self.stdout.write(self.style.SUCCESS(f'User {user.email} already has transactions. Skipping.'))
            return

        transactions_created = self._create_transactions(
            user=user,
            count=options['transactions'],
            days_back=options['days'],
        )
        self.stdout.write(self.style.SUCCESS(f'Transactions created for {user.email}: {transactions_created}'))

    def _create_categories(self) -> int:
        count = 0
        for name in EXPENSE_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=name,
                category_type=Category.CategoryType.EXPENSE,
                is_system=True,
                defaults={'user': None},
            )
            if created:
                count += 1

        for name in INCOME_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=name,
                category_type=Category.CategoryType.INCOME,
                is_system=True,
                defaults={'user': None},
            )
            if created:
                count += 1

        return count

    def _get_user(self, email: str | None):
        if email:
            return User.objects.filter(email=email).first()
        return User.objects.first()

    def _create_transactions(self, user, count: int, days_back: int) -> int:
        expense_cats = list(Category.objects.filter(
            category_type=Category.CategoryType.EXPENSE,
            is_system=True,
        ))
        income_cats = list(Category.objects.filter(
            category_type=Category.CategoryType.INCOME,
            is_system=True,
        ))

        if not expense_cats or not income_cats:
            self.stdout.write(self.style.WARNING('Categories are missing. Run setup_categories first.'))
            return 0

        payment_methods = [
            Transaction.PaymentMethod.CASH,
            Transaction.PaymentMethod.NON_CASH,
        ]
        org_activities = list(
            OrganizationActivity.objects.filter(profile__user=user).select_related('activity')
        )

        created = 0
        for _ in range(count):
            is_income = random.random() < 0.4
            if is_income:
                category = random.choice(income_cats)
                amount = random.randint(500, 150000) / 100
                descriptions = INCOME_DESCRIPTIONS + GENERIC_DESCRIPTIONS
            else:
                category = random.choice(expense_cats)
                amount = random.randint(100, 80000) / 100
                descriptions = EXPENSE_DESCRIPTIONS + GENERIC_DESCRIPTIONS

            description = random.choice(descriptions)[:100]
            is_business = bool(org_activities) and random.random() < 0.9
            activity_code = random.choice(org_activities).activity if is_business else None

            Transaction.objects.create(
                user=user,
                category=category,
                transaction_type=Transaction.TransactionType.INCOME if is_income else Transaction.TransactionType.EXPENSE,
                amount=amount,
                description=description,
                transaction_date=get_random_date(days_back),
                payment_method=random.choice(payment_methods),
                is_business=is_business,
                is_taxable=True,
                activity_code=activity_code,
            )
            created += 1

        return created
