#!/bin/sh
set -eu

if [ -z "${BOT_TOKEN:-}" ]; then
  echo "BOT_TOKEN is empty. Telegram bot is disabled."
  exec tail -f /dev/null
fi

exec python run_bot.py
