#!/usr/bin/env bash
# Linux/macOS: ./iniciar.sh bot   ou   ./iniciar.sh painel
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
case "$1" in
  bot) python -m app.bot ;;
  painel) streamlit run app/painel.py ;;
  backup) python -m app.backup ;;
  *) echo "Uso: ./iniciar.sh bot|painel|backup"; exit 1 ;;
esac
