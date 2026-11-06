"""Cópia de segurança do banco.

Uso:  python -m app.backup
Cria backups/financas-AAAA-MM-DD_HHMM.db e mantém só os 30 mais recentes.
Copie a pasta backups/ para um HD externo ou nuvem de tempos em tempos.
"""
import sqlite3

from app import config

MANTER = 30


def main():
    destino_dir = config.RAIZ / "backups"
    destino_dir.mkdir(exist_ok=True)
    destino = destino_dir / f"financas-{config.agora():%Y-%m-%d_%H%M}.db"
    origem = sqlite3.connect(config.DB_PATH)
    copia = sqlite3.connect(destino)
    with copia:
        origem.backup(copia)
    origem.close()
    copia.close()
    antigos = sorted(destino_dir.glob("financas-*.db"))[:-MANTER]
    for arq in antigos:
        arq.unlink()
    print(f"Backup criado: {destino}")


if __name__ == "__main__":
    main()
