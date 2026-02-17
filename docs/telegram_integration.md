1. Backend (Django)
Model: Add telegram_id (CharField, unique) to CustomUser.
Permissions: Use a custom class checking X-Bot-Secret header.
Endpoints:
GET /link/ (User JWT) → Returns t.me/bot?start=UUID.
POST /bot/link/ (Secret) → Binds UUID to TG_ID.
POST /bot/auth/ (Secret) → Exchanges TG_ID for User JWT.
2. Frontend (Web)
Fetch the link from /link/.
Display it as a button or QR code.
3. Bot (Python)
Linking: On /start UUID, send UUID + message.from_user.id to /bot/link/.
Action: Before calling finance API, get User JWT from /bot/auth/.
Refresh: If finance API returns 401, re-call /bot/auth/ and retry.
4. Requirements
Back: djangorestframework-simplejwt, django-environ.
Bot: aiogram, aiohttp, python-dotenv.