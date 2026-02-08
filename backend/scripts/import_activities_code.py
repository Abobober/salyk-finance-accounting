import pandas as pd
from users.models import ActivityCode
import re

def import_gked_from_excel(file_path):
    df = pd.read_excel(file_path, skiprows=3) # Пропускаем первые 3 строки (A1-A3)
    
    activities_to_create = []
    seen_codes = set()
    
    # Убедитесь, что имена столбцов соответствуют вашему файлу (например, 'Код', 'Секция', 'Наименование')
    # Замените 'Column A', 'Column B', 'Column C' на фактические заголовки
    CODE_COL = df.columns[0]
    SECTION_COL = df.columns[1]
    NAME_COL = df.columns[2]

    for _, row in df.iterrows():
        # Преобразуем в строку и удаляем лишние пробелы/типы данных
        code = str(row[CODE_COL]).strip()
        section = str(row[SECTION_COL]).strip()
        name = str(row[NAME_COL]).strip()

        # Пропускаем строки с пустыми ключевыми данными
        if not code or not section or not name:
            continue
            
        # 1. Фильтруем названия секций в ВЕРХНЕМ РЕГИСТРЕ (например, 'СЕЛЬСКОЕ ХОЗЯЙСТВО, ЛЕСНОЕ ХОЗЯЙСТВО И РЫБОЛОВСТВО')
        # Обычно они содержат запятые или пробелы, в отличие от реальных названий деятельности.
        if name.isupper() and (',' in name or ' ' in name):
             continue

        # 2. Фильтруем коды секций (A, B, AB и т.д.), которые не являются детализированными кодами ОКЭД (01, 01.1, ...)
        # Используем regex для проверки, что код содержит хотя бы одну цифру.
        if not bool(re.search(r'\d', code)):
             continue

        # 3. Обработка дубликатов кодов
        if code not in seen_codes:
            activities_to_create.append(
                ActivityCode(code=code, section=section, name=name)
            )
            seen_codes.add(code)

    ActivityCode.objects.bulk_create(activities_to_create, ignore_conflicts=True) # ignore_conflicts поможет при повторных запусках

# python manage.py shell
# Внутри оболочки:
# from scripts.import_activities_code import import_gked_from_excel
# import_gked_from_excel('./scripts/activity_codes_dict.xlsx')
# exit()