# Deploy on VPS

## 1. Prepare the server

- Install Docker Engine
- Install Docker Compose plugin
- Open inbound port `80`
- Optionally open port `443` if HTTPS will be terminated on the server

## 2. Upload the project

```bash
git clone <your-repository-url>
cd finance_accounting
```

## 3. Configure environment

Edit `.env.docker` and set at least:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_PASSWORD`

If Telegram bot is required, also set:

- `BOT_TOKEN`
- `BOT_API_SECRET`

If HTTPS is enabled on the public domain, also set:

- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`

## 4. Start the stack

```bash
docker compose up --build -d
```

## 5. Verify

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f gateway
```

Expected public URLs:

- `http://your-domain/`
- `http://your-domain/admin/`
- `http://your-domain/api/`

## 6. HTTPS options

The current stack exposes one HTTP entrypoint on port `80`.

Recommended options:

- Cloudflare Proxy in front of the server
- Nginx Proxy Manager on the VPS
- Caddy on the VPS

If HTTPS is terminated by an external reverse proxy, keep forwarding requests to this stack on port `80`.

## 7. Update the app

```bash
git pull
docker compose up --build -d
```
