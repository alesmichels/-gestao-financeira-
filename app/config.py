"""Configuração lida do arquivo .env (segredos) e do ambiente."""
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
GRUPO_AUTORIZADO = os.getenv("GRUPO_AUTORIZADO", "").strip()
DB_PATH = Path(os.getenv("DB_PATH", "dados/financas.db"))
if not DB_PATH.is_absolute():
    DB_PATH = RAIZ / DB_PATH
FUSO = ZoneInfo(os.getenv("FUSO", "America/Sao_Paulo"))
CADASTROS = RAIZ / "config" / "cadastros.json"
CADASTROS_EXEMPLO = RAIZ / "config" / "cadastros.example.json"


def agora() -> datetime:
    return datetime.now(FUSO)


def hoje():
    return agora().date()
