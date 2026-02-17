from django.core.management.base import BaseCommand
from finance.models import Category

class Command(BaseCommand):
    help = 'Создает стандартные системные категории для всех пользователей'

    def handle(self, *args, **options):
        expense_categories = [
            'Продукты', 'Транспорт', 'Коммунальные услуги', 'Аренда',
            'Зарплата сотрудникам', 'Реклама и маркетинг', 'Оборудование',
            'Канцелярия', 'Интернет и связь', 'Прочие расходы'
        ]
    
        income_categories = [
            'Продажа товаров', 'Оказание услуг', 'Аванс',
            'Инвестиции', 'Прочие доходы'
        ]

        count = 0
        # Создаем расходные категории
        for name in expense_categories:
            obj, created = Category.objects.get_or_create(
                name=name,
                category_type='expense',
                is_system=True,
                defaults={'user': None}
            )
            if created:
                count += 1

        # Создаем доходные категории
        for name in income_categories:
            obj, created = Category.objects.get_or_create(
                name=name,
                category_type='income',
                is_system=True,
                defaults={'user': None}
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Успешно добавлено {count} новых категорий.'))