from django.db import migrations

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('finance', 'Category')

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

    income_categories = [
        'Продажа товаров',
        'Оказание услуг',
        'Аванс',
        'Инвестиции',
        'Прочие доходы'
    ]

    for name in expense_categories:
        Category.objects.get_or_create(
            name=name,
            category_type='expense',
            is_system=True,
            defaults={'user': None}
        )

    for name in income_categories:
        Category.objects.get_or_create(
            name=name,
            category_type='income',
            is_system=True,
            defaults={'user': None}
        )


def reverse_func(apps, schema_editor):
    Category = apps.get_model('finance', 'Category')
    Category.objects.filter(is_system=True, user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_func),
    ]
