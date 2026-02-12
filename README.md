## Описание
Backend-система финансового учета для индивидуальных предпринимателей,
сдающих отчетность в Salyk.kg.

## Технологии
- Django + Django REST Framework
- PostgreSQL
- JWT Authentication

## Структура проекта
### Пользователь может:
- Регистрироваться
- Логиниться
- Разлогиниться
- Пройти онбординг:
1. Выбрать форму ведения бизнеса
2. Выбрать налоговый режим
3. Выбрать виды деятельности
4. Указать ставки налогов
- Открыть/настроить профиль
- Добавлять/удалять/изменять/просматривать транзакции
- Добавлять категории к транзакциям
- Добавлять/удалять/изменять категории
- Получать сводку по прибыли/расходам

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
5. Создать файл `.env` по примеру `env_example`
6. `python manage.py migrate`
7. `python manage.py runserver`

## Структура репозитория
- `main` - стабильная версия
- `develop` - ветка активной разработки

### Разработка

- Выбрать ветку разработки `git checkout develop`
- Првоерить на наличие обновлений `git pull origin develop`
- Переключиться на свою рабочую ветку `git checkout -b feature/name_of_feature`
- `git add .`
- `git commit -m "my_feature"`
- Когда готово, слить ветку в develop `git checkout develop`
- `git pull origin develop`
- `git merge feature/name_of_feature`
- Решить возможные конфликты
- `git add <file-with-conflicts>`
- `git commit -m "Resolved merge conflicts"`
- Запушить `git push origin develop`






