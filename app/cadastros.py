"""Aplica config/cadastros.json no banco.

Uso:  python -m app.cadastros
Se config/cadastros.json não existir, é criado a partir do exemplo.
"""
import json
import shutil

from app import config, db


def main():
    if not config.CADASTROS.exists():
        shutil.copy(config.CADASTROS_EXEMPLO, config.CADASTROS)
        print(f"Criei {config.CADASTROS.relative_to(config.RAIZ)} a partir do exemplo. "
              "Ajuste nomes, IDs do Telegram e cartões, e rode este comando de novo.")
    dados = json.loads(config.CADASTROS.read_text(encoding="utf-8"))
    con = db.conectar()
    uid = db.aplicar_cadastros(con, dados)
    sem_id = [p["nome"] for p in dados["pessoas"] if not p.get("telegram_id")]
    print(f"Cadastros aplicados na unidade '{dados['unidade']}' (id {uid}). Banco: {config.DB_PATH}")
    if sem_id:
        print("Atenção: sem ID do Telegram (o bot vai ignorar essas pessoas): " + ", ".join(sem_id))
        print("Mande /id para o bot no Telegram para descobrir o seu.")


if __name__ == "__main__":
    main()
