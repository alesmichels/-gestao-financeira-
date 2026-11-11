"""Banco de dados SQLite: esquema e operações.

Valores são guardados em centavos (inteiros) para evitar erro de arredondamento.
Datas são texto ISO (AAAA-MM-DD).
Toda alteração em lançamento gera uma linha em `historico`.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from app import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS unidades (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidades(id),
    nome TEXT NOT NULL,
    telegram_id INTEGER UNIQUE,
    peso_divisao REAL NOT NULL DEFAULT 0.5,
    ativo INTEGER NOT NULL DEFAULT 1,
    UNIQUE (unidade_id, nome)
);
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidades(id),
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('credito','debito','pix','vale','dinheiro')),
    titular_id INTEGER REFERENCES pessoas(id),
    dia_fechamento INTEGER,
    dia_vencimento INTEGER,
    apelidos TEXT NOT NULL DEFAULT '[]',
    ativo INTEGER NOT NULL DEFAULT 1,
    UNIQUE (unidade_id, nome)
);
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidades(id),
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'saida' CHECK (tipo IN ('saida','entrada')),
    regra_divisao TEXT NOT NULL DEFAULT 'proporcional'
        CHECK (regra_divisao IN ('proporcional','50/50','individual')),
    apelidos TEXT NOT NULL DEFAULT '[]',
    ativo INTEGER NOT NULL DEFAULT 1,
    UNIQUE (unidade_id, nome)
);
CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidades(id),
    data TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('saida','entrada')),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    descricao TEXT NOT NULL DEFAULT '',
    categoria_id INTEGER REFERENCES categorias(id),
    conta_id INTEGER REFERENCES contas(id),
    autor_id INTEGER REFERENCES pessoas(id),
    regra_divisao TEXT NOT NULL DEFAULT 'proporcional',
    origem TEXT NOT NULL DEFAULT 'telegram' CHECK (origem IN ('telegram','painel','importacao')),
    mensagem_origem TEXT,
    status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','confirmado','cancelado')),
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_lanc_data ON lancamentos (unidade_id, data);
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY,
    lancamento_id INTEGER NOT NULL REFERENCES lancamentos(id),
    acao TEXT NOT NULL,
    autor_id INTEGER REFERENCES pessoas(id),
    quando TEXT NOT NULL DEFAULT (datetime('now')),
    antes TEXT,
    depois TEXT
);
"""

CAMPOS_EDITAVEIS = {"data", "tipo", "valor_centavos", "descricao", "categoria_id",
                    "conta_id", "regra_divisao", "status"}


def conectar(caminho: Path | None = None) -> sqlite3.Connection:
    caminho = Path(caminho or config.DB_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


@contextmanager
def transacao(con: sqlite3.Connection):
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise


# ---------- cadastros ----------

def aplicar_cadastros(con: sqlite3.Connection, dados: dict) -> int:
    """Cria ou atualiza unidade, pessoas, contas e categorias a partir do JSON.
    Não apaga nada: itens removidos do JSON continuam no banco (histórico preservado)."""
    with transacao(con):
        con.execute("INSERT OR IGNORE INTO unidades (nome) VALUES (?)", (dados["unidade"],))
        uid = con.execute("SELECT id FROM unidades WHERE nome = ?", (dados["unidade"],)).fetchone()["id"]

        for p in dados["pessoas"]:
            tid = p.get("telegram_id") or None
            con.execute(
                """INSERT INTO pessoas (unidade_id, nome, telegram_id, peso_divisao)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT (unidade_id, nome) DO UPDATE SET
                     telegram_id = excluded.telegram_id, peso_divisao = excluded.peso_divisao""",
                (uid, p["nome"], tid, p.get("peso_divisao", 0.5)),
            )
        pessoas = {r["nome"]: r["id"] for r in con.execute(
            "SELECT id, nome FROM pessoas WHERE unidade_id = ?", (uid,))}

        for c in dados["contas"]:
            con.execute(
                """INSERT INTO contas (unidade_id, nome, tipo, titular_id, dia_fechamento, dia_vencimento, apelidos)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (unidade_id, nome) DO UPDATE SET
                     tipo = excluded.tipo, titular_id = excluded.titular_id,
                     dia_fechamento = excluded.dia_fechamento, dia_vencimento = excluded.dia_vencimento,
                     apelidos = excluded.apelidos""",
                (uid, c["nome"], c["tipo"], pessoas.get(c.get("titular")),
                 c.get("dia_fechamento"), c.get("dia_vencimento"),
                 json.dumps(c.get("apelidos", []), ensure_ascii=False)),
            )

        for c in dados["categorias"]:
            con.execute(
                """INSERT INTO categorias (unidade_id, nome, tipo, regra_divisao, apelidos)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT (unidade_id, nome) DO UPDATE SET
                     tipo = excluded.tipo, regra_divisao = excluded.regra_divisao, apelidos = excluded.apelidos""",
                (uid, c["nome"], c.get("tipo", "saida"), c.get("regra_divisao", "proporcional"),
                 json.dumps(c.get("apelidos", []), ensure_ascii=False)),
            )
    return uid


def unidade_padrao(con) -> int:
    row = con.execute("SELECT id FROM unidades ORDER BY id LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError("Nenhuma unidade cadastrada. Rode: python -m app.cadastros")
    return row["id"]


def pessoas(con, unidade_id, incluir_inativos=False):
    filtro = "" if incluir_inativos else " AND ativo = 1"
    return con.execute(f"SELECT * FROM pessoas WHERE unidade_id = ?{filtro} ORDER BY id",
                       (unidade_id,)).fetchall()


def pessoa_por_telegram(con, telegram_id):
    return con.execute("SELECT * FROM pessoas WHERE telegram_id = ? AND ativo = 1",
                       (telegram_id,)).fetchone()


def contas(con, unidade_id, incluir_inativos=False):
    filtro = "" if incluir_inativos else " AND ativo = 1"
    return con.execute(f"SELECT * FROM contas WHERE unidade_id = ?{filtro} ORDER BY id",
                       (unidade_id,)).fetchall()


def categorias(con, unidade_id, tipo=None, incluir_inativos=False):
    sql = "SELECT * FROM categorias WHERE unidade_id = ?" + ("" if incluir_inativos else " AND ativo = 1")
    args = [unidade_id]
    if tipo:
        sql += " AND tipo = ?"
        args.append(tipo)
    return con.execute(sql + " ORDER BY id", args).fetchall()


def categoria_por_nome(con, unidade_id, nome):
    return con.execute("SELECT * FROM categorias WHERE unidade_id = ? AND nome = ?",
                       (unidade_id, nome)).fetchone()


# ---------- lançamentos ----------

def criar_lancamento(con, *, unidade_id, data: date, tipo, valor_centavos, descricao,
                     categoria_id, conta_id, autor_id, regra_divisao, origem="telegram",
                     mensagem_origem=None, status="pendente") -> int:
    with transacao(con):
        cur = con.execute(
            """INSERT INTO lancamentos (unidade_id, data, tipo, valor_centavos, descricao, categoria_id,
                 conta_id, autor_id, regra_divisao, origem, mensagem_origem, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (unidade_id, data.isoformat(), tipo, valor_centavos, descricao, categoria_id, conta_id,
             autor_id, regra_divisao, origem, mensagem_origem, status),
        )
        lid = cur.lastrowid
        con.execute("INSERT INTO historico (lancamento_id, acao, autor_id, depois) VALUES (?, 'criado', ?, ?)",
                    (lid, autor_id, json.dumps(_linha(con, lid), ensure_ascii=False)))
    return lid


def atualizar_lancamento(con, lancamento_id, autor_id=None, acao="editado", **campos):
    invalidos = set(campos) - CAMPOS_EDITAVEIS
    if invalidos:
        raise ValueError(f"Campos não editáveis: {invalidos}")
    if "data" in campos and isinstance(campos["data"], date):
        campos["data"] = campos["data"].isoformat()
    with transacao(con):
        antes = _linha(con, lancamento_id)
        if antes is None:
            raise ValueError("Lançamento não encontrado")
        sets = ", ".join(f"{k} = ?" for k in campos)
        con.execute(f"UPDATE lancamentos SET {sets}, atualizado_em = datetime('now') WHERE id = ?",
                    (*campos.values(), lancamento_id))
        depois = _linha(con, lancamento_id)
        con.execute("INSERT INTO historico (lancamento_id, acao, autor_id, antes, depois) VALUES (?, ?, ?, ?, ?)",
                    (lancamento_id, acao, autor_id, json.dumps(antes, ensure_ascii=False),
                     json.dumps(depois, ensure_ascii=False)))


def _linha(con, lancamento_id):
    r = con.execute("SELECT * FROM lancamentos WHERE id = ?", (lancamento_id,)).fetchone()
    return dict(r) if r else None


def lancamento(con, lancamento_id):
    return con.execute(
        """SELECT l.*, c.nome AS categoria, k.nome AS conta, k.tipo AS conta_tipo, p.nome AS autor
           FROM lancamentos l
           LEFT JOIN categorias c ON c.id = l.categoria_id
           LEFT JOIN contas k ON k.id = l.conta_id
           LEFT JOIN pessoas p ON p.id = l.autor_id
           WHERE l.id = ?""", (lancamento_id,)).fetchone()


def lancamentos_periodo(con, unidade_id, inicio: date, fim: date, status=("confirmado",)):
    """Lançamentos com data entre inicio e fim (inclusive)."""
    marcas = ",".join("?" * len(status))
    return con.execute(
        f"""SELECT l.*, c.nome AS categoria, k.nome AS conta, k.tipo AS conta_tipo,
                   k.titular_id AS conta_titular_id, p.nome AS autor
            FROM lancamentos l
            LEFT JOIN categorias c ON c.id = l.categoria_id
            LEFT JOIN contas k ON k.id = l.conta_id
            LEFT JOIN pessoas p ON p.id = l.autor_id
            WHERE l.unidade_id = ? AND l.data BETWEEN ? AND ? AND l.status IN ({marcas})
            ORDER BY l.data DESC, l.id DESC""",
        (unidade_id, inicio.isoformat(), fim.isoformat(), *status)).fetchall()


def pendentes(con, unidade_id):
    return con.execute(
        """SELECT l.*, p.nome AS autor FROM lancamentos l LEFT JOIN pessoas p ON p.id = l.autor_id
           WHERE l.unidade_id = ? AND l.status = 'pendente' ORDER BY l.id""", (unidade_id,)).fetchall()


def ultimo_do_autor(con, autor_id):
    return con.execute(
        """SELECT * FROM lancamentos WHERE autor_id = ? AND status != 'cancelado'
           ORDER BY id DESC LIMIT 1""", (autor_id,)).fetchone()


# ---------- edição de cadastros pelo aplicativo ----------

def _texto_para_apelidos(texto) -> str:
    if isinstance(texto, list):
        lista = texto
    else:
        lista = [a.strip() for a in str(texto or "").split(",")]
    return json.dumps([a for a in lista if a], ensure_ascii=False)


def apelidos_para_texto(bruto) -> str:
    return ", ".join(json.loads(bruto or "[]"))


def _validar_nomes(linhas):
    nomes = [str(l.get("nome") or "").strip() for l in linhas]
    if any(not n for n in nomes):
        raise ValueError("Toda linha precisa de um nome.")
    repetidos = {n for n in nomes if nomes.count(n) > 1}
    if repetidos:
        raise ValueError(f"Nomes repetidos: {', '.join(sorted(repetidos))}")


def salvar_pessoas(con, unidade_id, linhas: list[dict]):
    """Cada linha: id (None = nova), nome, peso_divisao, telegram_id, ativo."""
    _validar_nomes(linhas)
    with transacao(con):
        for l in linhas:
            valores = (l["nome"].strip(), float(l.get("peso_divisao") or 0),
                       int(l["telegram_id"]) if l.get("telegram_id") else None, int(bool(l.get("ativo", True))))
            if l.get("id"):
                con.execute("UPDATE pessoas SET nome = ?, peso_divisao = ?, telegram_id = ?, ativo = ? "
                            "WHERE id = ? AND unidade_id = ?", (*valores, int(l["id"]), unidade_id))
            else:
                con.execute("INSERT INTO pessoas (nome, peso_divisao, telegram_id, ativo, unidade_id) "
                            "VALUES (?, ?, ?, ?, ?)", (*valores, unidade_id))


def salvar_contas(con, unidade_id, linhas: list[dict]):
    """Cada linha: id, nome, tipo, titular (nome ou vazio), dia_fechamento, dia_vencimento, apelidos, ativo."""
    _validar_nomes(linhas)
    ids_pessoa = {p["nome"]: p["id"] for p in pessoas(con, unidade_id, incluir_inativos=True)}
    with transacao(con):
        for l in linhas:
            if l.get("tipo") not in ("credito", "debito", "pix", "vale", "dinheiro"):
                raise ValueError(f"Tipo inválido em '{l['nome']}'.")
            dia_f = int(l["dia_fechamento"]) if l.get("dia_fechamento") else None
            dia_v = int(l["dia_vencimento"]) if l.get("dia_vencimento") else None
            for dia in (dia_f, dia_v):
                if dia is not None and not 1 <= dia <= 31:
                    raise ValueError(f"Dia inválido em '{l['nome']}': use 1 a 31.")
            valores = (l["nome"].strip(), l["tipo"], ids_pessoa.get(l.get("titular") or ""), dia_f, dia_v,
                       _texto_para_apelidos(l.get("apelidos")), int(bool(l.get("ativo", True))))
            if l.get("id"):
                con.execute("UPDATE contas SET nome = ?, tipo = ?, titular_id = ?, dia_fechamento = ?, "
                            "dia_vencimento = ?, apelidos = ?, ativo = ? WHERE id = ? AND unidade_id = ?",
                            (*valores, int(l["id"]), unidade_id))
            else:
                con.execute("INSERT INTO contas (nome, tipo, titular_id, dia_fechamento, dia_vencimento, apelidos, "
                            "ativo, unidade_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (*valores, unidade_id))


def salvar_categorias(con, unidade_id, linhas: list[dict]):
    """Cada linha: id, nome, tipo, regra_divisao, apelidos, ativo."""
    _validar_nomes(linhas)
    with transacao(con):
        for l in linhas:
            if l.get("tipo") not in ("saida", "entrada"):
                raise ValueError(f"Tipo inválido em '{l['nome']}'.")
            if l.get("regra_divisao") not in ("proporcional", "50/50", "individual"):
                raise ValueError(f"Divisão inválida em '{l['nome']}'.")
            valores = (l["nome"].strip(), l["tipo"], l["regra_divisao"],
                       _texto_para_apelidos(l.get("apelidos")), int(bool(l.get("ativo", True))))
            if l.get("id"):
                con.execute("UPDATE categorias SET nome = ?, tipo = ?, regra_divisao = ?, apelidos = ?, ativo = ? "
                            "WHERE id = ? AND unidade_id = ?", (*valores, int(l["id"]), unidade_id))
            else:
                con.execute("INSERT INTO categorias (nome, tipo, regra_divisao, apelidos, ativo, unidade_id) "
                            "VALUES (?, ?, ?, ?, ?, ?)", (*valores, unidade_id))
