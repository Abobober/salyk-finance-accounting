## Описание
Backend-система финансового учета для индивидуальных предпринимателей, сдающих отчетность в `Salyk.kg`.

## Технологии
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Redis
- Celery

## Инициализация
1. Создать виртуальное окружение: `python -m venv venv`
2. Активировать его: `venv\Scripts\activate`
3. Установить зависимости: `pip install -r requirements.txt`
4. Создать `.env` по примеру `env_example`
5. Выполнить миграции: `python manage.py migrate`
6. Запустить backend: `python manage.py runserver`

## Быстрый запуск
```powershell
.\scripts\run_dev.ps1
```

Скрипт применяет миграции, импортирует справочники, при необходимости заполняет демо-данные и запускает backend, Telegram-бота и frontend.

Если нужен dev-superuser, заранее задайте `DJANGO_SUPERUSER_EMAIL` и `DJANGO_SUPERUSER_PASSWORD`.

Для фоновых задач проект использует локальный Redis на `redis://127.0.0.1:6379/0` и Celery.

## Основные возможности backend
- регистрация и JWT-аутентификация
- onboarding организации
- справочник видов деятельности
- учет транзакций и категорий
- аналитика и налоговые сводки
