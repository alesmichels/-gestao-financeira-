"""Cadastros iniciais (pessoas, contas, categorias).

O aplicativo aplica os cadastros sozinho na primeira vez que abre. Depois disso,
tudo se ajusta pela página Configurações do aplicativo.

Uso opcional, para reaplicar o arquivo JSON:  python -m app.cadastros
Se config/cadastros.json existir, ele é usado; senão, config/cadastros.example.json.
"""
import json

from app import config, db


def arquivo_de_cadastros():
    return config.CADASTROS if config.CADASTROS.exists() else config.CADASTROS_EXEMPLO


def garantir_cadastros(con) -> int:
    """Na primeira execução (banco vazio), aplica os cadastros iniciais. Devolve o id da unidade."""
    row = con.execute("SELECT id FROM unidades ORDER BY id LIMIT 1").fetchone()
    if row:
        return row["id"]
    dados = json.loads(arquivo_de_cadastros().read_text(encoding="utf-8"))
    return db.aplicar_cadastros(con, dados)


def main():
    origem = arquivo_de_cadastros()
    dados = json.loads(origem.read_text(encoding="utf-8"))
    con = db.conectar()
    uid = db.aplicar_cadastros(con, dados)
    print(f"Cadastros de {origem.name} aplicados na unidade '{dados['unidade']}' (id {uid}).")
    print(f"Banco: {config.DB_PATH}")


if __name__ == "__main__":
    main()
