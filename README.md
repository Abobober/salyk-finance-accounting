## Описание
Веб приложение для финансового учета для индивидуальных предпринимателей,
сдающих отчетность в Salyk.kg.

## Технологии
- Django + Django REST Framework
- PostgreSQL
- JWT Authentication

## Структура проекта


## Что делать
### Создание локальн БД:
1. PostgreSQL 18.1 https://www.postgresql.org/download/windows/
2. В SQL Shell (psql): Enter на всех вопросах, ввести пароль.
3. Там же - `CREATE DATABASE salyk_finance_db;` `\q`

### Инициализация
1. Клонировать репозиторий
2. `python -m venv venv`
3. `venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Создать файл `.env` по примеру `.env.example`
6. `python manage.py migrate`
7. `python manage.py runserver`

## Структура репозитория
- `main` - стабильная версия
- `develop` - ветка активной разработки

### Разработка в develop
- `git checkout develop`
- `git pull`
- `git checkout -b feature/name_of_feature`

- `git add .`
- `git commit -m "my_feature"`
- `git push origin feature/name_of_feature`






