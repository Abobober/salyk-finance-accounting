"""
Импорт кодов деятельности (ГКЭД) из Excel.
Пропускает импорт, если данные уже загружены.
Использование: python manage.py import_activities_code [--file PATH]
"""
import os

from django.core.management.base import BaseCommand

from activities.models import ActivityCode


class Command(BaseCommand):
    help = 'Импорт кодов деятельности из Excel (пропуск, если данные уже есть)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Путь к Excel-файлу (по умолчанию: activities/scripts/activity_codes_dict.xlsx)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Импортировать даже если данные уже есть',
        )

    def handle(self, *args, **options):
        if ActivityCode.objects.exists() and not options['force']:
            self.stdout.write(self.style.SUCCESS('Коды деятельности уже загружены. Пропуск.'))
            return

        file_path = options['file']
        if not file_path:
            # Относительно backend/
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(base, 'activities', 'scripts', 'activity_codes_dict.xlsx')

        if not os.path.isfile(file_path):
            self.stdout.write(self.style.WARNING(f'Файл не найден: {file_path}. Пропуск импорта.'))
            return

        try:
            from activities.scripts.import_activities_code import import_gked_from_excel
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Ошибка импорта: {e}'))
            return

        import_gked_from_excel(file_path)
        count = ActivityCode.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Импортировано кодов деятельности: {count}'))
