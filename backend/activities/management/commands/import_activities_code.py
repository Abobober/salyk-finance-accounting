"""
Import activity codes from the bundled Excel file.

Skips import when data already exists unless --force is provided.
Usage: python manage.py import_activities_code [--file PATH]
"""
import os

from django.core.management.base import BaseCommand

from activities.models import ActivityCode


class Command(BaseCommand):
    help = 'Import activity codes from Excel and skip when data already exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Path to the Excel file. Defaults to activities/scripts/activity_codes_dict.xlsx',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Import even when activity codes already exist',
        )

    def handle(self, *args, **options):
        if ActivityCode.objects.exists() and not options['force']:
            self.stdout.write(self.style.SUCCESS('Activity codes already exist. Skipping import.'))
            return

        file_path = options['file']
        if not file_path:
            # Resolve from backend/activities/management/commands/ -> backend/activities/
            app_root = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
            file_path = os.path.join(app_root, 'scripts', 'activity_codes_dict.xlsx')

        if not os.path.isfile(file_path):
            self.stdout.write(self.style.WARNING(f'File not found: {file_path}. Skipping import.'))
            return

        try:
            from activities.scripts.import_activities_code import import_gked_from_excel
        except ImportError as exc:
            self.stdout.write(self.style.ERROR(f'Import error: {exc}'))
            return

        import_gked_from_excel(file_path)
        count = ActivityCode.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Imported activity codes: {count}'))
