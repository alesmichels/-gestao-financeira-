#!/usr/bin/env bash
# Linux/macOS: ./iniciar.sh app | backup | bot
set -e
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
case "${1:-app}" in
  app) .venv/bin/python -m streamlit run app/painel.py ;;
  backup) .venv/bin/python -m app.backup ;;
  bot) .venv/bin/pip install -q -r requirements-bot.txt && .venv/bin/python -m app.bot ;;
  *) echo "Uso: ./iniciar.sh app|backup|bot"; exit 1 ;;
esac
