# Finance Accounting

Backend-система финансового учета для индивидуальных предпринимателей c учетом транзакций, аналитикой, налоговыми сводками, Telegram-интеграцией.

## Технологии

- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Redis
- Celery
- Telegram Bot API
- OpenRouter API


## Структура репозитория

- `backend/` - Django backend
- `frontend/` - клиентская часть
- `tg_bot/` - Telegram-бот
- `scripts/` - dev-скрипты
- `docs/` - техническая документация


## Установка зависимостей

### Создание локальной БД:
1. PostgreSQL 18.1 https://www.postgresql.org/download/windows/
2. В SQL Shell (psql): Enter на всех вопросах, ввести пароль.
3. Там же - `CREATE DATABASE salyk_finance_db;` `\q`


### Redis

- можно поставить так:

```powershell
winget install Redis.Redis
```

Проверка:

```powershell
"C:\Program Files\Redis\redis-cli.exe" ping
```

Ожидаемый ответ:

```text
PONG
```

## Переменные окружения

Создайте `.env` в корне проекта по примеру [env_example]

Минимально нужно заполнить:

- `SECRET_KEY`
- `DEBUG`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Опционально:

- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`
- `BOT_USERNAME`
- `FINANCE_CACHE_TTL`
- `IDEMPOTENCY_ENABLED`
- `IDEMPOTENCY_CACHE_TTL`
- `IDEMPOTENCY_LOCK_TTL`

Пример локальных значений для Redis/Celery:

```env
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

## Инициализация проекта

Из корня репозитория:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

После этого:

```powershell
cd backend
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py import_activities_code
```

Если нужен dev-superuser, заранее задайте:

```powershell
$env:DJANGO_SUPERUSER_EMAIL="admin@example.com"
$env:DJANGO_SUPERUSER_PASSWORD="StrongPass123!"
```

И затем выполните:

```powershell
..\venv\Scripts\python.exe manage.py ensure_superuser
```

## Запуск backend вручную

Из папки `backend`:

```powershell
..\venv\Scripts\python.exe manage.py runserver
```

Backend будет доступен на `http://127.0.0.1:8000`.

## Запуск Celery вручную

Из папки `backend` в отдельных окнах:

```powershell
..\venv\Scripts\python.exe -m celery -A config worker -l info -P solo
```

```powershell
..\venv\Scripts\python.exe -m celery -A config beat -l info
```

## Быстрый dev-запуск

Из корня проекта:

```powershell
.\scripts\run_dev.ps1
```

Скрипт:

- применяет миграции
- создает superuser, если заданы `DJANGO_SUPERUSER_EMAIL` и `DJANGO_SUPERUSER_PASSWORD`
- импортирует справочник видов деятельности
- заполняет demo-данные при необходимости
- запускает backend
- запускает Celery worker
- запускает Celery beat
- запускает Telegram-бота
- запускает frontend

## Полезные management commands

Из папки `backend`:

```powershell
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py import_activities_code
..\venv\Scripts\python.exe manage.py setup_demo_data --skip-if-populated
..\venv\Scripts\python.exe manage.py ensure_superuser
..\venv\Scripts\python.exe manage.py test users finance organization telegram_bot
..\venv\Scripts\python.exe manage.py check
```

## GitHub Flow

### Основные ветки

- `main` - стабильная ветка
- `develop` - основная ветка активной разработки

### Как добавлять новый функционал

1. Переключиться на `develop`
2. Подтянуть актуальное состояние
3. Создать свою ветку от `develop`
4. Сделать изменения
5. Прогнать проверки локально
6. Запушить ветку в origin
7. Открыть PR в `develop`

Пример:

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/short-description
```

После изменений:

```powershell
git add .
git commit -m "feat: short description"
git push origin feature/short-description
```