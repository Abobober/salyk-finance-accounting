# Салыйк — Фронтенд

Фронтенд для системы финансового учёта ИП (Salyk.kg).

## Стек

- React 18 + TypeScript
- Vite
- React Router
- openapi-typescript (для генерации типов из OpenAPI-схемы)

## Запуск

```bash
npm install
npm run dev
```

Приложение: http://localhost:3000

Бэкенд должен быть запущен на http://localhost:8000 (прокси настроен для `/api`).

## Генерация типов API

При изменении бэкенда пересоберите типы:

```bash
# Бэкенд должен быть запущен
npm run generate:api
```

- Текущая схема: drf-yasg → http://localhost:8000/swagger.json/
- Если перейдёте на drf-spectacular, измените скрипт в `package.json` на `/api/schema/`
