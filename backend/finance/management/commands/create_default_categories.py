from django.core.management.base import BaseCommand
from finance.models import Category


class Command(BaseCommand):
    help = 'Создает системные категории по умолчанию'
    
    def handle(self, *args, **options):
        # Системные категории расходов
        expense_categories = [
            'Продукты',
            'Транспорт',
            'Коммунальные услуги',
            'Аренда',
            'Зарплата сотрудникам',
            'Реклама и маркетинг',
            'Оборудование',
            'Канцелярия',
            'Интернет и связь',
            'Налоги',
            'Прочие расходы'
        ]
        
        # Системные категории доходов
        income_categories = [
            'Продажа товаров',
            'Оказание услуг',
            'Аванс',
            'Инвестиции',
            'Прочие доходы'
        ]
        
        # Создаем категории расходов
        for name in expense_categories:
            Category.objects.get_or_create(
                name=name,
                category_type=Category.EXPENSE,
                is_system=True,
                defaults={'user': None}
            )
        
        # Создаем категории доходов
        for name in income_categories:
            Category.objects.get_or_create(
                name=name,
                category_type=Category.INCOME,
                is_system=True,
                defaults={'user': None}
            )
        
        self.stdout.write(
            self.style.SUCCESS('Системные категории успешно созданы!')
        )