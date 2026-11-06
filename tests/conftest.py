import json
from pathlib import Path

import pytest

from app import db

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def cadastros():
    return json.loads((RAIZ / "config" / "cadastros.example.json").read_text(encoding="utf-8"))


@pytest.fixture
def con(tmp_path, cadastros):
    cadastros["pessoas"][0]["telegram_id"] = 111
    cadastros["pessoas"][1]["telegram_id"] = 222
    c = db.conectar(tmp_path / "teste.db")
    db.aplicar_cadastros(c, cadastros)
    return c


@pytest.fixture
def uid(con):
    return db.unidade_padrao(con)
