"""Aplicativo no navegador.

Uso:  streamlit run app/painel.py   (ou dois cliques em abrir-aplicativo.bat)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import config, db  # noqa: E402
from app.cadastros import garantir_cadastros  # noqa: E402
from app.paginas import configuracoes, lancamentos, visao_geral  # noqa: E402
from app.paginas.comum import Contexto  # noqa: E402
from app.servico import MESES  # noqa: E402

st.set_page_config(page_title="Gestão Financeira", layout="wide")

con = db.conectar()
uid = garantir_cadastros(con)
hoje = config.hoje()

with st.sidebar:
    st.title("Gestão Financeira")
    unidade = con.execute("SELECT nome FROM unidades WHERE id = ?", (uid,)).fetchone()["nome"]
    st.caption(f"Unidade: {unidade}")
    pessoas = {p["id"]: dict(p) for p in db.pessoas(con, uid)}
    pessoa_id = st.selectbox("Quem está lançando", list(pessoas), key="quem",
                             format_func=lambda i: pessoas[i]["nome"]) if pessoas else None
    meses = []
    a, m = hoje.year, hoje.month
    for _ in range(24):
        meses.append((a, m))
        a, m = (a, m - 1) if m > 1 else (a - 1, 12)
    ano, mes = st.selectbox("Mês", meses, key="mes", format_func=lambda x: f"{MESES[x[1] - 1]} {x[0]}")

ctx = Contexto(con=con, uid=uid, hoje=hoje, pessoa=pessoas.get(pessoa_id), ano=ano, mes=mes)

pagina = st.navigation([
    st.Page(lambda: visao_geral.render(ctx), title="Visão geral", icon=":material/dashboard:",
            url_path="visao-geral", default=True),
    st.Page(lambda: lancamentos.render(ctx), title="Lançamentos", icon=":material/edit_note:",
            url_path="lancamentos"),
    st.Page(lambda: configuracoes.render(ctx), title="Configurações", icon=":material/settings:",
            url_path="configuracoes"),
])
pagina.run()
